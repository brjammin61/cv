#region Using declarations
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.ComponentModel.DataAnnotations;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Input;
using System.Windows.Media;
using System.Xml.Serialization;
using NinjaTrader.Cbi;
using NinjaTrader.Gui;
using NinjaTrader.Gui.Chart;
using NinjaTrader.Gui.SuperDom;
using NinjaTrader.Gui.Tools;
using NinjaTrader.Data;
using NinjaTrader.NinjaScript;
using NinjaTrader.Core.FloatingPoint;
using NinjaTrader.NinjaScript.Indicators;
using NinjaTrader.NinjaScript.DrawingTools;
using NetMQ;
using NetMQ.Sockets;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
#endregion

// =============================================================================
// THE CORTEX PROTOCOL - EXECUTION LAYER ("THE BODY")
// =============================================================================
//
// Architecture: Event-Driven Online Learning Trading Engine
// Role: Execute trades, manage risk, feed data to Python Brain
//
// Communication Protocol:
// - PREDICT: Sent on every bar close with feature vector
// - TRAIN: Sent immediately after trade closes with PnL
//
// Dependencies:
// - NetMQ.dll (NuGet: Install-Package NetMQ)
// - Newtonsoft.Json.dll (usually included in NT8)
//
// =============================================================================

namespace NinjaTrader.NinjaScript.Strategies
{
    public class CortexMasterStrategy : Strategy
    {
        // =====================================================================
        // ZeroMQ Connection
        // =====================================================================
        private RequestSocket cortexClient;
        private bool isConnected = false;
        private int connectionAttempts = 0;
        private const int MAX_CONNECTION_ATTEMPTS = 3;

        // =====================================================================
        // Indicators
        // =====================================================================
        private ATR atrIndicator;
        private RSI rsiIndicator;
        private SMA volumeSMA;

        // =====================================================================
        // VWAP Calculation (Manual - more control than built-in)
        // =====================================================================
        private double cumulativeTPV;       // Cumulative (Typical Price * Volume)
        private double cumulativeVolume;    // Cumulative Volume
        private double vwap;
        private double vwapStdDev;
        private List<double> vwapDeviations;
        private DateTime sessionStart;

        // =====================================================================
        // Position Tracking
        // =====================================================================
        private bool wasFlat = true;
        private double entryPrice = 0;
        private int entryContracts = 0;
        private DateTime entryTime;

        // =====================================================================
        // Risk Management
        // =====================================================================
        private double sessionPnL = 0;
        private int tradesThisSession = 0;

        // =====================================================================
        // Parameters
        // =====================================================================

        [NinjaScriptProperty]
        [Display(Name = "Cortex Server Address", GroupName = "Cortex Protocol", Order = 1)]
        public string CortexServerAddress { get; set; } = "tcp://localhost:5555";

        [NinjaScriptProperty]
        [Display(Name = "VWAP StdDev Multiplier", GroupName = "VWAP Strategy", Order = 1)]
        public double StdDevMultiplier { get; set; } = 2.0;

        [NinjaScriptProperty]
        [Display(Name = "Stop Loss (Ticks)", GroupName = "Risk Management", Order = 1)]
        public int StopLossTicks { get; set; } = 25;

        [NinjaScriptProperty]
        [Display(Name = "Profit Target (Ticks)", GroupName = "Risk Management", Order = 2)]
        public int ProfitTargetTicks { get; set; } = 15;

        [NinjaScriptProperty]
        [Display(Name = "Daily Loss Limit", GroupName = "Risk Management", Order = 3)]
        public double DailyLossLimit { get; set; } = 1000;

        [NinjaScriptProperty]
        [Display(Name = "Max Trades Per Day", GroupName = "Risk Management", Order = 4)]
        public int MaxTradesPerDay { get; set; } = 10;

        // =====================================================================
        // State Machine
        // =====================================================================
        protected override void OnStateChange()
        {
            if (State == State.SetDefaults)
            {
                Description = "Cortex Protocol - Event-Driven Online Learning Trading Engine";
                Name = "CortexMasterStrategy";
                Calculate = Calculate.OnBarClose;
                EntriesPerDirection = 1;
                EntryHandling = EntryHandling.AllEntries;
                IsExitOnSessionCloseStrategy = true;
                ExitOnSessionCloseSeconds = 30;
                IsFillLimitOnTouch = false;
                MaximumBarsLookBack = MaximumBarsLookBack.TwoHundredFiftySix;
                OrderFillResolution = OrderFillResolution.Standard;
                Slippage = 2;
                StartBehavior = StartBehavior.WaitUntilFlat;
                TimeInForce = TimeInForce.Gtc;
                TraceOrders = false;
                RealtimeErrorHandling = RealtimeErrorHandling.StopCancelClose;
                StopTargetHandling = StopTargetHandling.PerEntryExecution;
                BarsRequiredToTrade = 50;
                IsUnmanaged = false;
            }
            else if (State == State.Configure)
            {
                // Add ATR for volatility
                atrIndicator = ATR(14);

                // Add RSI for momentum
                rsiIndicator = RSI(14, 3);

                // Volume SMA for comparison
                volumeSMA = SMA(Volume, 20);
            }
            else if (State == State.DataLoaded)
            {
                // Initialize VWAP tracking
                vwapDeviations = new List<double>();
                ResetVWAP();

                // Connect to Cortex Brain
                ConnectToCortex();
            }
            else if (State == State.Terminated)
            {
                // Clean up ZeroMQ connection
                DisconnectFromCortex();
            }
        }

        // =====================================================================
        // VWAP Calculation Methods
        // =====================================================================
        private void ResetVWAP()
        {
            cumulativeTPV = 0;
            cumulativeVolume = 0;
            vwap = 0;
            vwapStdDev = 0;
            vwapDeviations.Clear();
            sessionStart = Time[0].Date;
        }

        private void UpdateVWAP()
        {
            // Reset VWAP at session start
            if (Time[0].Date != sessionStart)
            {
                ResetVWAP();
                sessionPnL = 0;
                tradesThisSession = 0;
            }

            // Typical Price
            double typicalPrice = (High[0] + Low[0] + Close[0]) / 3.0;

            // Update cumulative values
            cumulativeTPV += typicalPrice * Volume[0];
            cumulativeVolume += Volume[0];

            // Calculate VWAP
            if (cumulativeVolume > 0)
                vwap = cumulativeTPV / cumulativeVolume;
            else
                vwap = Close[0];

            // Track deviations for StdDev calculation
            double deviation = Close[0] - vwap;
            vwapDeviations.Add(deviation);

            // Keep only last 100 deviations for StdDev
            if (vwapDeviations.Count > 100)
                vwapDeviations.RemoveAt(0);

            // Calculate StdDev
            if (vwapDeviations.Count >= 20)
            {
                double mean = vwapDeviations.Average();
                double sumSquares = vwapDeviations.Sum(d => Math.Pow(d - mean, 2));
                vwapStdDev = Math.Sqrt(sumSquares / vwapDeviations.Count);
            }
        }

        // =====================================================================
        // Cortex Connection Methods
        // =====================================================================
        private void ConnectToCortex()
        {
            try
            {
                cortexClient = new RequestSocket();
                cortexClient.Connect(CortexServerAddress);

                // Test connection with STATUS request
                var testRequest = new { type = "STATUS" };
                string response = SendToCortex(JsonConvert.SerializeObject(testRequest));

                if (!string.IsNullOrEmpty(response) && response.Contains("ONLINE"))
                {
                    isConnected = true;
                    Print("✅ CORTEX CONNECTED: Brain online and ready");
                }
                else
                {
                    Print("⚠️ CORTEX WARNING: Connected but brain not responding correctly");
                }
            }
            catch (Exception e)
            {
                Print($"❌ CORTEX CONNECTION FAILED: {e.Message}");
                isConnected = false;
                connectionAttempts++;
            }
        }

        private void DisconnectFromCortex()
        {
            if (cortexClient != null)
            {
                try
                {
                    cortexClient.Disconnect(CortexServerAddress);
                    cortexClient.Dispose();
                    Print("🔌 CORTEX DISCONNECTED");
                }
                catch { }
            }
        }

        private string SendToCortex(string jsonMessage)
        {
            if (cortexClient == null) return "{}";

            try
            {
                cortexClient.SendFrame(jsonMessage);

                // Receive with timeout (5 seconds)
                string response;
                if (cortexClient.TryReceiveFrameString(TimeSpan.FromSeconds(5), out response))
                {
                    return response;
                }
                else
                {
                    Print("⚠️ CORTEX TIMEOUT: No response in 5 seconds");
                    return "{}";
                }
            }
            catch (Exception e)
            {
                Print($"❌ CORTEX SEND ERROR: {e.Message}");
                return "{}";
            }
        }

        // =====================================================================
        // Main Trading Logic
        // =====================================================================
        protected override void OnBarUpdate()
        {
            // Skip if not enough bars
            if (CurrentBar < BarsRequiredToTrade) return;

            // Update VWAP
            UpdateVWAP();

            // Calculate bands
            double upperBand = vwap + (vwapStdDev * StdDevMultiplier);
            double lowerBand = vwap - (vwapStdDev * StdDevMultiplier);

            // Calculate momentum (10-bar rate of change)
            double momentum = CurrentBar >= 10 ? (Close[0] - Close[10]) / Close[10] : 0;

            // =================================================================
            // RISK CHECKS
            // =================================================================

            // Check daily loss limit
            if (sessionPnL <= -DailyLossLimit)
            {
                if (Position.MarketPosition != MarketPosition.Flat)
                    ExitLong("DailyLimit_Exit", "CortexLong");
                return;
            }

            // Check max trades
            if (tradesThisSession >= MaxTradesPerDay)
                return;

            // =================================================================
            // CONSTRUCT FEATURE VECTOR FOR CORTEX
            // =================================================================
            var features = new
            {
                close = Close[0],
                atr = atrIndicator[0],
                rsi = rsiIndicator[0],
                volume = Volume[0],
                volume_ratio = volumeSMA[0] > 0 ? Volume[0] / volumeSMA[0] : 1.0,
                hour = Time[0].Hour,
                vwap = vwap,
                vwap_dist = Close[0] - vwap,
                upper_band = upperBand,
                lower_band = lowerBand,
                momentum = momentum
            };

            // =================================================================
            // ASK THE CORTEX BRAIN (PREDICT)
            // =================================================================
            if (Position.MarketPosition == MarketPosition.Flat && isConnected)
            {
                string jsonRequest = JsonConvert.SerializeObject(new
                {
                    type = "PREDICT",
                    features = features
                });

                string response = SendToCortex(jsonRequest);

                try
                {
                    JObject signal = JObject.Parse(response);
                    string signalType = signal["signal"]?.ToString() ?? "WAIT";
                    int contracts = signal["contracts"]?.Value<int>() ?? 0;
                    double confidence = signal["confidence"]?.Value<double>() ?? 0;
                    string regime = signal["regime"]?.ToString() ?? "UNKNOWN";

                    // =================================================================
                    // EXECUTE TRADING SIGNAL
                    // =================================================================
                    if (signalType == "GO" && contracts > 0)
                    {
                        // Check VWAP conditions (Baseline filter - strategy confirmation)
                        bool longSetup = Close[0] <= lowerBand;
                        bool shortSetup = Close[0] >= upperBand;

                        if (longSetup)
                        {
                            entryContracts = contracts;
                            SetStopLoss("CortexLong", CalculationMode.Ticks, StopLossTicks, false);
                            SetProfitTarget("CortexLong", CalculationMode.Ticks, ProfitTargetTicks);
                            EnterLong(contracts, "CortexLong");

                            Print($"🟢 CORTEX LONG: {contracts} contracts @ {Close[0]:F2} | " +
                                  $"Confidence: {confidence:P0} | Regime: {regime}");
                        }
                        else if (shortSetup)
                        {
                            entryContracts = contracts;
                            SetStopLoss("CortexShort", CalculationMode.Ticks, StopLossTicks, false);
                            SetProfitTarget("CortexShort", CalculationMode.Ticks, ProfitTargetTicks);
                            EnterShort(contracts, "CortexShort");

                            Print($"🔴 CORTEX SHORT: {contracts} contracts @ {Close[0]:F2} | " +
                                  $"Confidence: {confidence:P0} | Regime: {regime}");
                        }
                    }
                    else if (signalType == "WAIT")
                    {
                        string reason = signal["reason"]?.ToString() ?? "Unknown";
                        // Optionally log wait signals
                        // Print($"⏸️ WAIT: {reason}");
                    }
                }
                catch (Exception e)
                {
                    Print($"❌ PARSE ERROR: {e.Message}");
                }
            }
        }

        // =====================================================================
        // THE REFLEX: Immediate Feedback Loop
        // =====================================================================
        protected override void OnPositionUpdate(Cbi.Position position, double averagePrice,
            int quantity, Cbi.MarketPosition marketPosition)
        {
            // Detect when position closes (goes to Flat)
            bool isNowFlat = (position.MarketPosition == MarketPosition.Flat);

            if (isNowFlat && !wasFlat)
            {
                // Position just closed - calculate PnL and send to Cortex

                double pnl = 0;

                // Get PnL from last trade
                if (SystemPerformance.AllTrades.Count > 0)
                {
                    var lastTrade = SystemPerformance.AllTrades[SystemPerformance.AllTrades.Count - 1];
                    pnl = lastTrade.ProfitCurrency;
                }

                // Update session tracking
                sessionPnL += pnl;
                tradesThisSession++;

                // =================================================================
                // SEND TRAINING DATA TO CORTEX (THE REFLEX)
                // =================================================================
                if (isConnected)
                {
                    var trainingData = new
                    {
                        type = "TRAIN",
                        pnl = pnl,
                        contracts = entryContracts,
                        session_pnl = sessionPnL,
                        trades_today = tradesThisSession
                    };

                    string response = SendToCortex(JsonConvert.SerializeObject(trainingData));

                    string emoji = pnl >= 0 ? "✅" : "❌";
                    Print($"🎓 CORTEX LEARNED: {emoji} PnL=${pnl:F2} | " +
                          $"Session=${sessionPnL:F2} | Trades={tradesThisSession}");

                    // Log drift detection if present
                    try
                    {
                        JObject result = JObject.Parse(response);
                        string drift = result["drift"]?.ToString() ?? "STABLE";
                        if (drift == "DRIFT_DETECTED")
                        {
                            Print("⚠️ CORTEX ALERT: Market regime shift detected!");
                        }
                    }
                    catch { }
                }
            }

            wasFlat = isNowFlat;
        }

        // =====================================================================
        // Execution Update (for managed orders)
        // =====================================================================
        protected override void OnExecutionUpdate(Cbi.Execution execution, string executionId,
            double price, int quantity, Cbi.MarketPosition marketPosition,
            string orderId, DateTime time)
        {
            if (execution.Order.Name.Contains("Cortex"))
            {
                entryPrice = price;
                entryTime = time;
            }
        }
    }
}
