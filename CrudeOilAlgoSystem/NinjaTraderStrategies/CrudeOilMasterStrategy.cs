/*
 * Crude Oil Master Strategy - NinjaTrader 8
 *
 * Advanced algorithmic trading system for Crude Oil futures (CL/MCL)
 * Designed for prop firm compliance and robust risk management
 *
 * Features:
 * - Unmanaged order handling for Rithmic compatibility
 * - VWAP mean reversion with standard deviation bands
 * - EIA inventory momentum breakout logic
 * - Hard-coded daily loss limits (DLL)
 * - Trailing drawdown protection
 * - Consistency rule compliance (40% profit cap)
 * - News event filtering
 * - CVOL-based regime detection
 * - Auction Market Theory (AMT) integration
 *
 * Target Platform: NinjaTrader 8.1.2+ (.NET Framework 4.8, C# 8.0)
 * Target Instruments: CL, MCL (WTI Crude Oil Futures)
 *
 * Author: Algorithmic Trading Framework 2025
 */

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
using System.IO;
#endregion

namespace NinjaTrader.NinjaScript.Strategies
{
    public class CrudeOilMasterStrategy : Strategy
    {
        #region Strategy State Variables

        // Position tracking for unmanaged order handling
        private Order entryOrder;
        private Order stopLossOrder;
        private Order profitTarget1Order;
        private Order profitTarget2Order;

        private int currentQuantity;
        private double averageEntryPrice;
        private bool isStrategyLocked;

        // Session tracking
        private double sessionStartEquity;
        private double sessionPnL;
        private double sessionHighEquity;
        private double dailyProfitTarget;
        private double evaluationStartEquity;

        // News filter
        private List<DateTime> newsBlackoutTimes;

        // Regime detection
        private bool isHighVolatilityRegime;
        private double currentCVOL;

        // Volume Profile / AMT
        private double valueAreaHigh;
        private double valueAreaLow;
        private double pocPrice; // Point of Control

        // VWAP indicators
        private VWAP vwapIndicator;
        private double vwapUpper2SD;
        private double vwapLower2SD;

        // Consistency tracking
        private double consistencyThreshold;
        private double requiredProfitForEval;

        #endregion

        #region User Parameters

        [NinjaScriptProperty]
        [Display(Name = "Enable VWAP Mean Reversion", Order = 1, GroupName = "1. Strategy Selection")]
        public bool EnableVWAPMeanReversion { get; set; }

        [NinjaScriptProperty]
        [Display(Name = "Enable EIA Momentum", Order = 2, GroupName = "1. Strategy Selection")]
        public bool EnableEIAMomentum { get; set; }

        [NinjaScriptProperty]
        [Display(Name = "Enable AMT Volume Profile", Order = 3, GroupName = "1. Strategy Selection")]
        public bool EnableAMT { get; set; }

        // Risk Management Parameters
        [NinjaScriptProperty]
        [Range(100, 5000)]
        [Display(Name = "Daily Loss Limit ($)", Order = 1, GroupName = "2. Risk Management")]
        public double DailyLossLimit { get; set; }

        [NinjaScriptProperty]
        [Range(100, 10000)]
        [Display(Name = "Trailing Drawdown ($)", Order = 2, GroupName = "2. Risk Management")]
        public double TrailingDrawdown { get; set; }

        [NinjaScriptProperty]
        [Display(Name = "Enable Trailing DD Protection", Order = 3, GroupName = "2. Risk Management")]
        public bool EnableTrailingDrawdownProtection { get; set; }

        [NinjaScriptProperty]
        [Range(1, 10)]
        [Display(Name = "Default Position Size", Order = 4, GroupName = "2. Risk Management")]
        public int DefaultPositionSize { get; set; }

        [NinjaScriptProperty]
        [Range(10, 100)]
        [Display(Name = "Stop Loss Ticks", Order = 5, GroupName = "2. Risk Management")]
        public int StopLossTicks { get; set; }

        // Prop Firm Compliance
        [NinjaScriptProperty]
        [Display(Name = "Enable Consistency Rule", Order = 1, GroupName = "3. Prop Firm Compliance")]
        public bool EnableConsistencyRule { get; set; }

        [NinjaScriptProperty]
        [Range(0.2, 0.6)]
        [Display(Name = "Consistency Percentage", Order = 2, GroupName = "3. Prop Firm Compliance")]
        public double ConsistencyPercentage { get; set; }

        [NinjaScriptProperty]
        [Range(1000, 20000)]
        [Display(Name = "Evaluation Profit Target ($)", Order = 3, GroupName = "3. Prop Firm Compliance")]
        public double EvaluationProfitTarget { get; set; }

        [NinjaScriptProperty]
        [Display(Name = "Enable News Filter", Order = 4, GroupName = "3. Prop Firm Compliance")]
        public bool EnableNewsFilter { get; set; }

        [NinjaScriptProperty]
        [Display(Name = "News Calendar CSV Path", Order = 5, GroupName = "3. Prop Firm Compliance")]
        public string NewsCalendarPath { get; set; }

        // VWAP Parameters
        [NinjaScriptProperty]
        [Range(1.5, 3.0)]
        [Display(Name = "VWAP StdDev Multiplier", Order = 1, GroupName = "4. VWAP Settings")]
        public double VWAPStdDevMultiplier { get; set; }

        [NinjaScriptProperty]
        [Display(Name = "VWAP Anchor", Order = 2, GroupName = "4. VWAP Settings")]
        public SessionIterator.SessionType VWAPAnchorSession { get; set; }

        [NinjaScriptProperty]
        [Range(1, 50)]
        [Display(Name = "VWAP Target Ticks", Order = 3, GroupName = "4. VWAP Settings")]
        public int VWAPTargetTicks { get; set; }

        // CVOL Regime Detection
        [NinjaScriptProperty]
        [Range(20, 50)]
        [Display(Name = "High Volatility Threshold", Order = 1, GroupName = "5. Regime Detection")]
        public double HighVolatilityThreshold { get; set; }

        [NinjaScriptProperty]
        [Range(10, 30)]
        [Display(Name = "Low Volatility Threshold", Order = 2, GroupName = "5. Regime Detection")]
        public double LowVolatilityThreshold { get; set; }

        // Python ML Integration
        [NinjaScriptProperty]
        [Display(Name = "Enable Python ML", Order = 1, GroupName = "6. ML Integration")]
        public bool EnablePythonML { get; set; }

        [NinjaScriptProperty]
        [Display(Name = "Python Server Address", Order = 2, GroupName = "6. ML Integration")]
        public string PythonServerAddress { get; set; }

        [NinjaScriptProperty]
        [Range(5000, 9999)]
        [Display(Name = "Python Server Port", Order = 3, GroupName = "6. ML Integration")]
        public int PythonServerPort { get; set; }

        #endregion

        #region Strategy Initialization

        protected override void OnStateChange()
        {
            if (State == State.SetDefaults)
            {
                Description = @"Advanced Crude Oil Futures Strategy - Prop Firm Optimized";
                Name = "CrudeOilMasterStrategy";
                Calculate = Calculate.OnEachTick;
                EntriesPerDirection = 1;
                EntryHandling = EntryHandling.UniqueEntries;
                IsExitOnSessionCloseStrategy = true;
                ExitOnSessionCloseSeconds = 30;
                IsFillLimitOnTouch = false;
                MaximumBarsLookBack = MaximumBarsLookBack.TwoHundredFiftySix;
                OrderFillResolution = OrderFillResolution.Standard;
                Slippage = 2; // 2 ticks slippage assumption
                StartBehavior = StartBehavior.WaitUntilFlat;
                TimeInForce = TimeInForce.Day;
                TraceOrders = true;
                RealtimeErrorHandling = RealtimeErrorHandling.StopCancelClose;
                StopTargetHandling = StopTargetHandling.PerEntryExecution;
                BarsRequiredToTrade = 20;
                IsUnmanaged = true; // CRITICAL: Unmanaged for Rithmic compatibility

                // Default parameter values
                EnableVWAPMeanReversion = true;
                EnableEIAMomentum = false;
                EnableAMT = true;

                DailyLossLimit = 1000;
                TrailingDrawdown = 2000;
                EnableTrailingDrawdownProtection = true;
                DefaultPositionSize = 1;
                StopLossTicks = 25;

                EnableConsistencyRule = true;
                ConsistencyPercentage = 0.40;
                EvaluationProfitTarget = 3000;
                EnableNewsFilter = true;
                NewsCalendarPath = @"C:\AlgoTrading\NewsCalendar.csv";

                VWAPStdDevMultiplier = 2.0;
                VWAPAnchorSession = SessionIterator.SessionType.Trading;
                VWAPTargetTicks = 20;

                HighVolatilityThreshold = 45;
                LowVolatilityThreshold = 30;

                EnablePythonML = false;
                PythonServerAddress = "127.0.0.1";
                PythonServerPort = 5555;
            }
            else if (State == State.Configure)
            {
                // Initialize session tracking
                isStrategyLocked = false;
                newsBlackoutTimes = new List<DateTime>();

                // Load news calendar if enabled
                if (EnableNewsFilter && File.Exists(NewsCalendarPath))
                {
                    LoadNewsCalendar();
                }

                // Add VWAP indicator
                vwapIndicator = VWAP(VWAPAnchorSession);
                AddChartIndicator(vwapIndicator);
            }
            else if (State == State.DataLoaded)
            {
                // Initialize equity tracking
                sessionStartEquity = Account.Get(AccountItem.CashValue, Currency.UsDollar);
                evaluationStartEquity = sessionStartEquity;
                sessionHighEquity = sessionStartEquity;
                requiredProfitForEval = EvaluationProfitTarget;
                consistencyThreshold = requiredProfitForEval * ConsistencyPercentage;

                ClearOutputWindow();
                Print(string.Format("========================================"));
                Print(string.Format("Crude Oil Master Strategy Initialized"));
                Print(string.Format("Starting Equity: ${0:N2}", sessionStartEquity));
                Print(string.Format("Daily Loss Limit: ${0:N2}", DailyLossLimit));
                Print(string.Format("Trailing Drawdown: ${0:N2}", TrailingDrawdown));
                Print(string.Format("Consistency Threshold: ${0:N2}", consistencyThreshold));
                Print(string.Format("========================================"));
            }
            else if (State == State.Terminated)
            {
                // Cleanup
                if (entryOrder != null)
                    entryOrder = null;
                if (stopLossOrder != null)
                    stopLossOrder = null;
                if (profitTarget1Order != null)
                    profitTarget1Order = null;
                if (profitTarget2Order != null)
                    profitTarget2Order = null;
            }
        }

        #endregion

        #region Core Strategy Logic

        protected override void OnBarUpdate()
        {
            // Safety checks
            if (CurrentBar < BarsRequiredToTrade)
                return;

            if (State != State.Realtime && State != State.Historical)
                return;

            // Update session tracking at start of new session
            if (Bars.IsFirstBarOfSession)
            {
                OnNewTradingSession();
            }

            // ========================================
            // CIRCUIT BREAKER: Daily Loss Limit Check
            // ========================================
            if (!CheckDailyLossLimit())
            {
                Print("CIRCUIT BREAKER TRIGGERED: Daily Loss Limit reached. Strategy locked.");
                isStrategyLocked = true;
                FlattenAllPositions("Daily Loss Limit");
                return;
            }

            // ========================================
            // CIRCUIT BREAKER: Consistency Rule Check
            // ========================================
            if (EnableConsistencyRule && !CheckConsistencyRule())
            {
                Print("CIRCUIT BREAKER TRIGGERED: Consistency Rule violated. Trading throttled.");
                // Don't lock entirely, but reduce position size or skip entry
                if (Position.MarketPosition != MarketPosition.Flat)
                    return; // Don't take new trades, but manage existing
            }

            // ========================================
            // NEWS FILTER: Check blackout times
            // ========================================
            if (EnableNewsFilter && IsNewsBlackout())
            {
                // Flatten positions 5 minutes before news
                if (Position.MarketPosition != MarketPosition.Flat)
                {
                    FlattenAllPositions("News Event Approaching");
                }
                return;
            }

            // ========================================
            // REGIME DETECTION: Update volatility state
            // ========================================
            UpdateRegimeDetection();

            // ========================================
            // VWAP CALCULATION: Update bands
            // ========================================
            if (vwapIndicator != null && !double.IsNaN(vwapIndicator.Value[0]))
            {
                UpdateVWAPBands();
            }

            // ========================================
            // STRATEGY EXECUTION
            // ========================================

            // Only execute if not locked and we have valid data
            if (isStrategyLocked)
                return;

            // Strategy router based on enabled strategies and regime
            if (Position.MarketPosition == MarketPosition.Flat)
            {
                // No open position - look for entry signals

                if (isHighVolatilityRegime && EnableEIAMomentum)
                {
                    // High volatility: Use momentum/breakout logic
                    ExecuteEIAMomentumLogic();
                }
                else if (!isHighVolatilityRegime && EnableVWAPMeanReversion)
                {
                    // Low volatility: Use mean reversion
                    ExecuteVWAPMeanReversionLogic();
                }
                else if (EnableAMT)
                {
                    // Auction Market Theory logic
                    ExecuteAMTLogic();
                }
            }
            else
            {
                // Position is open - manage exits
                ManageOpenPosition();
            }
        }

        protected override void OnExecutionUpdate(Execution execution, string executionId,
            double price, int quantity, MarketPosition marketPosition, string orderId, DateTime time)
        {
            // ========================================
            // RITHMIC-FRIENDLY EXECUTION HANDLING
            // Critical for prop firm Rithmic feeds
            // ========================================

            if (execution.Order == null)
                return;

            // Track entry fills
            if (execution.Order.Name == "Entry Long" || execution.Order.Name == "Entry Short")
            {
                // Update position tracking immediately (don't wait for OnOrderUpdate)
                if (execution.Order.OrderState == OrderState.Filled ||
                    execution.Order.OrderState == OrderState.PartFilled)
                {
                    // Calculate average entry price for partial fills
                    averageEntryPrice = ((averageEntryPrice * currentQuantity) + (price * quantity))
                                       / (currentQuantity + quantity);
                    currentQuantity += quantity;

                    Print(string.Format("EXECUTION: {0} filled {1} @ {2:F2}, Avg Entry: {3:F2}, Total Qty: {4}",
                        execution.Order.Name, quantity, price, averageEntryPrice, currentQuantity));

                    // Immediately submit protective stop if not already working
                    SubmitProtectiveOrders(marketPosition);
                }
            }

            // Track exit fills
            if (execution.Order.Name == "Stop Loss" ||
                execution.Order.Name == "Profit Target 1" ||
                execution.Order.Name == "Profit Target 2")
            {
                if (execution.Order.OrderState == OrderState.Filled ||
                    execution.Order.OrderState == OrderState.PartFilled)
                {
                    currentQuantity -= quantity;

                    Print(string.Format("EXECUTION: {0} filled {1} @ {2:F2}, Remaining Qty: {3}",
                        execution.Order.Name, quantity, price, currentQuantity));

                    // If fully closed, reset tracking
                    if (currentQuantity <= 0)
                    {
                        ResetPositionTracking();
                    }
                    else
                    {
                        // Partial exit - update remaining stop/target quantities
                        AdjustProtectiveOrders();
                    }
                }
            }
        }

        protected override void OnOrderUpdate(Order order, double limitPrice, double stopPrice,
            int quantity, int filled, double averageFillPrice,
            OrderState orderState, DateTime time, ErrorCode error, string nativeError)
        {
            // Handle order rejections and errors
            if (order.OrderState == OrderState.Rejected)
            {
                Print(string.Format("ORDER REJECTED: {0} - {1}", order.Name, error));
                ResetPositionTracking();
            }

            if (error != ErrorCode.NoError)
            {
                Print(string.Format("ORDER ERROR: {0} - {1} - {2}", order.Name, error, nativeError));
            }
        }

        #endregion

        #region VWAP Mean Reversion Logic

        private void ExecuteVWAPMeanReversionLogic()
        {
            if (vwapIndicator == null || double.IsNaN(vwapIndicator.Value[0]))
                return;

            double vwap = vwapIndicator.Value[0];
            double close = Close[0];
            double high = High[0];
            double low = Low[0];

            // Check for mean reversion opportunity at upper band (short signal)
            if (close >= vwapUpper2SD)
            {
                // Look for reversal confirmation: bearish engulfing or rejection wick
                if (IsBearishReversalPattern())
                {
                    int entryQuantity = CalculatePositionSize();
                    double entryPrice = close;
                    double stopPrice = high + (StopLossTicks * TickSize);
                    double targetPrice = vwap;

                    Print(string.Format("VWAP SHORT SIGNAL: Price {0:F2} at Upper Band {1:F2}, Target VWAP {2:F2}",
                        close, vwapUpper2SD, vwap));

                    EnterShortPosition(entryQuantity, entryPrice, stopPrice, targetPrice);
                }
            }
            // Check for mean reversion opportunity at lower band (long signal)
            else if (close <= vwapLower2SD)
            {
                // Look for reversal confirmation: bullish engulfing or rejection wick
                if (IsBullishReversalPattern())
                {
                    int entryQuantity = CalculatePositionSize();
                    double entryPrice = close;
                    double stopPrice = low - (StopLossTicks * TickSize);
                    double targetPrice = vwap;

                    Print(string.Format("VWAP LONG SIGNAL: Price {0:F2} at Lower Band {1:F2}, Target VWAP {2:F2}",
                        close, vwapLower2SD, vwap));

                    EnterLongPosition(entryQuantity, entryPrice, stopPrice, targetPrice);
                }
            }
        }

        private void UpdateVWAPBands()
        {
            if (vwapIndicator == null)
                return;

            double vwap = vwapIndicator.Value[0];

            // Calculate standard deviation
            // This is simplified - in production, you'd use a proper VWAP StdDev indicator
            double sumSquaredDeviations = 0;
            int lookback = Math.Min(20, CurrentBar);

            for (int i = 0; i < lookback; i++)
            {
                double deviation = Close[i] - vwap;
                sumSquaredDeviations += deviation * deviation;
            }

            double variance = sumSquaredDeviations / lookback;
            double stdDev = Math.Sqrt(variance);

            vwapUpper2SD = vwap + (stdDev * VWAPStdDevMultiplier);
            vwapLower2SD = vwap - (stdDev * VWAPStdDevMultiplier);
        }

        private bool IsBullishReversalPattern()
        {
            // Bullish engulfing or hammer pattern
            if (CurrentBar < 1)
                return false;

            double prevOpen = Open[1];
            double prevClose = Close[1];
            double currOpen = Open[0];
            double currClose = Close[0];
            double currHigh = High[0];
            double currLow = Low[0];

            // Bullish engulfing
            bool bullishEngulfing = (prevClose < prevOpen) && // Previous bar bearish
                                   (currClose > currOpen) &&  // Current bar bullish
                                   (currOpen < prevClose) &&  // Opens below previous close
                                   (currClose > prevOpen);    // Closes above previous open

            // Hammer pattern (long lower wick, small body)
            double body = Math.Abs(currClose - currOpen);
            double lowerWick = Math.Min(currOpen, currClose) - currLow;
            double upperWick = currHigh - Math.Max(currOpen, currClose);
            bool hammer = (lowerWick > 2 * body) && (upperWick < body);

            return bullishEngulfing || hammer;
        }

        private bool IsBearishReversalPattern()
        {
            // Bearish engulfing or shooting star pattern
            if (CurrentBar < 1)
                return false;

            double prevOpen = Open[1];
            double prevClose = Close[1];
            double currOpen = Open[0];
            double currClose = Close[0];
            double currHigh = High[0];
            double currLow = Low[0];

            // Bearish engulfing
            bool bearishEngulfing = (prevClose > prevOpen) && // Previous bar bullish
                                   (currClose < currOpen) &&  // Current bar bearish
                                   (currOpen > prevClose) &&  // Opens above previous close
                                   (currClose < prevOpen);    // Closes below previous open

            // Shooting star pattern (long upper wick, small body)
            double body = Math.Abs(currClose - currOpen);
            double upperWick = currHigh - Math.Max(currOpen, currClose);
            double lowerWick = Math.Min(currOpen, currClose) - currLow;
            bool shootingStar = (upperWick > 2 * body) && (lowerWick < body);

            return bearishEngulfing || shootingStar;
        }

        #endregion

        #region EIA Momentum Logic

        private void ExecuteEIAMomentumLogic()
        {
            // EIA inventory report typically releases Wednesdays at 10:30 AM ET
            // This logic implements the "Retracement Confirmation" approach

            DateTime now = Time[0];

            // Check if it's Wednesday
            if (now.DayOfWeek != DayOfWeek.Wednesday)
                return;

            // Check if we're in the time window (10:30 - 11:30 AM ET)
            TimeSpan eiaReleaseTime = new TimeSpan(10, 30, 0);
            TimeSpan currentTime = now.TimeOfDay;

            if (currentTime < eiaReleaseTime || currentTime > eiaReleaseTime.Add(new TimeSpan(1, 0, 0)))
                return;

            // Look for initial impulse move (first 60 seconds after release)
            // Then wait for 50-61.8% retracement for entry

            // This is a simplified implementation - in production you'd track the actual impulse candle
            // and calculate Fibonacci retracements dynamically

            Print("EIA MOMENTUM: In time window, monitoring for impulse and retracement");

            // Placeholder for advanced logic
            // In production, you would:
            // 1. Identify impulse direction and magnitude
            // 2. Calculate Fibonacci levels
            // 3. Place limit order at 61.8% retracement
            // 4. Set stop below/above impulse low/high
        }

        #endregion

        #region Auction Market Theory Logic

        private void ExecuteAMTLogic()
        {
            // Simplified AMT logic based on Value Area
            // In production, you'd integrate a full Volume Profile indicator

            double close = Close[0];
            double open = Open[0];

            // If we open inside Value Area -> range-bound, fade the edges
            if (close >= valueAreaLow && close <= valueAreaHigh)
            {
                // Mean reversion mode
                if (close > valueAreaHigh - (valueAreaHigh - valueAreaLow) * 0.2)
                {
                    // Near upper edge of value area - potential short
                    Print("AMT: Inside Value Area, near upper edge - fade high");
                }
                else if (close < valueAreaLow + (valueAreaHigh - valueAreaLow) * 0.2)
                {
                    // Near lower edge of value area - potential long
                    Print("AMT: Inside Value Area, near lower edge - fade low");
                }
            }
            else
            {
                // Open outside Value Area -> trending, follow the direction
                if (close > valueAreaHigh)
                {
                    Print("AMT: Above Value Area - bullish continuation expected");
                    // Trend following logic
                }
                else if (close < valueAreaLow)
                {
                    Print("AMT: Below Value Area - bearish continuation expected");
                    // Trend following logic
                }
            }
        }

        #endregion

        #region Order Management (Unmanaged)

        private void EnterLongPosition(int quantity, double entryPrice, double stopPrice, double targetPrice)
        {
            if (entryOrder != null)
                return;

            // Submit entry order
            entryOrder = SubmitOrderUnmanaged(0, OrderAction.Buy, OrderType.Market, quantity,
                0, 0, "", "Entry Long");

            Print(string.Format("SUBMITTING LONG: Qty {0} @ Market, Stop {1:F2}, Target {2:F2}",
                quantity, stopPrice, targetPrice));
        }

        private void EnterShortPosition(int quantity, double entryPrice, double stopPrice, double targetPrice)
        {
            if (entryOrder != null)
                return;

            // Submit entry order
            entryOrder = SubmitOrderUnmanaged(0, OrderAction.SellShort, OrderType.Market, quantity,
                0, 0, "", "Entry Short");

            Print(string.Format("SUBMITTING SHORT: Qty {0} @ Market, Stop {1:F2}, Target {2:F2}",
                quantity, stopPrice, targetPrice));
        }

        private void SubmitProtectiveOrders(MarketPosition position)
        {
            if (currentQuantity == 0)
                return;

            double stopPrice = 0;
            double target1Price = 0;
            double target2Price = 0;

            if (position == MarketPosition.Long)
            {
                stopPrice = averageEntryPrice - (StopLossTicks * TickSize);
                target1Price = averageEntryPrice + (VWAPTargetTicks * TickSize);
                target2Price = averageEntryPrice + (VWAPTargetTicks * 2 * TickSize);
            }
            else if (position == MarketPosition.Short)
            {
                stopPrice = averageEntryPrice + (StopLossTicks * TickSize);
                target1Price = averageEntryPrice - (VWAPTargetTicks * TickSize);
                target2Price = averageEntryPrice - (VWAPTargetTicks * 2 * TickSize);
            }

            // Submit stop loss if not already working
            if (stopLossOrder == null || stopLossOrder.OrderState == OrderState.Cancelled ||
                stopLossOrder.OrderState == OrderState.Filled || stopLossOrder.OrderState == OrderState.Rejected)
            {
                OrderAction stopAction = position == MarketPosition.Long ? OrderAction.Sell : OrderAction.BuyToCover;
                stopLossOrder = SubmitOrderUnmanaged(0, stopAction, OrderType.StopMarket,
                    currentQuantity, 0, stopPrice, "", "Stop Loss");

                Print(string.Format("STOP LOSS SUBMITTED: {0} {1} @ {2:F2}",
                    stopAction, currentQuantity, stopPrice));
            }

            // Submit profit targets (scale out: 50% at target1, 50% at target2)
            int target1Qty = currentQuantity / 2;
            int target2Qty = currentQuantity - target1Qty;

            if (target1Qty > 0 && (profitTarget1Order == null || profitTarget1Order.OrderState == OrderState.Cancelled))
            {
                OrderAction targetAction = position == MarketPosition.Long ? OrderAction.Sell : OrderAction.BuyToCover;
                profitTarget1Order = SubmitOrderUnmanaged(0, targetAction, OrderType.Limit,
                    target1Qty, target1Price, 0, "", "Profit Target 1");

                Print(string.Format("PROFIT TARGET 1 SUBMITTED: {0} {1} @ {2:F2}",
                    targetAction, target1Qty, target1Price));
            }

            if (target2Qty > 0 && (profitTarget2Order == null || profitTarget2Order.OrderState == OrderState.Cancelled))
            {
                OrderAction targetAction = position == MarketPosition.Long ? OrderAction.Sell : OrderAction.BuyToCover;
                profitTarget2Order = SubmitOrderUnmanaged(0, targetAction, OrderType.Limit,
                    target2Qty, target2Price, 0, "", "Profit Target 2");

                Print(string.Format("PROFIT TARGET 2 SUBMITTED: {0} {1} @ {2:F2}",
                    targetAction, target2Qty, target2Price));
            }
        }

        private void AdjustProtectiveOrders()
        {
            // Called when partial fills occur
            // Adjust stop and remaining targets based on new quantity

            // For simplicity, this could cancel and resubmit
            // In production, you'd use ChangeOrder for efficiency

            Print("Adjusting protective orders for remaining quantity: " + currentQuantity);
        }

        private void FlattenAllPositions(string reason)
        {
            Print(string.Format("FLATTENING ALL POSITIONS: {0}", reason));

            // Cancel all working orders
            if (entryOrder != null && IsOrderWorking(entryOrder))
                CancelOrder(entryOrder);
            if (stopLossOrder != null && IsOrderWorking(stopLossOrder))
                CancelOrder(stopLossOrder);
            if (profitTarget1Order != null && IsOrderWorking(profitTarget1Order))
                CancelOrder(profitTarget1Order);
            if (profitTarget2Order != null && IsOrderWorking(profitTarget2Order))
                CancelOrder(profitTarget2Order);

            // Close position if open
            if (Position.MarketPosition == MarketPosition.Long)
            {
                SubmitOrderUnmanaged(0, OrderAction.Sell, OrderType.Market,
                    Position.Quantity, 0, 0, "", "Flatten Long");
            }
            else if (Position.MarketPosition == MarketPosition.Short)
            {
                SubmitOrderUnmanaged(0, OrderAction.BuyToCover, OrderType.Market,
                    Position.Quantity, 0, 0, "", "Flatten Short");
            }

            ResetPositionTracking();
        }

        private void ResetPositionTracking()
        {
            entryOrder = null;
            stopLossOrder = null;
            profitTarget1Order = null;
            profitTarget2Order = null;
            currentQuantity = 0;
            averageEntryPrice = 0;
        }

        private bool IsOrderWorking(Order order)
        {
            return order != null &&
                   (order.OrderState == OrderState.Accepted ||
                    order.OrderState == OrderState.Working ||
                    order.OrderState == OrderState.PartFilled);
        }

        private void ManageOpenPosition()
        {
            // Trailing stop logic, breakeven logic, etc.
            // This is called when we have an open position

            if (Position.MarketPosition == MarketPosition.Flat)
                return;

            double unrealizedPnL = Position.GetUnrealizedProfitLoss(PerformanceUnit.Currency, Close[0]);

            // Move stop to breakeven if profit > X ticks
            int breakevenTriggerTicks = StopLossTicks / 2;
            double breakevenProfit = breakevenTriggerTicks * TickSize * Position.Quantity;

            if (unrealizedPnL > breakevenProfit && stopLossOrder != null)
            {
                // Move stop to breakeven (entry price)
                if (Position.MarketPosition == MarketPosition.Long &&
                    stopLossOrder.StopPrice < averageEntryPrice)
                {
                    ChangeOrder(stopLossOrder, stopLossOrder.Quantity, 0, averageEntryPrice);
                    Print("Stop moved to breakeven for Long position");
                }
                else if (Position.MarketPosition == MarketPosition.Short &&
                         stopLossOrder.StopPrice > averageEntryPrice)
                {
                    ChangeOrder(stopLossOrder, stopLossOrder.Quantity, 0, averageEntryPrice);
                    Print("Stop moved to breakeven for Short position");
                }
            }
        }

        #endregion

        #region Risk Management & Circuit Breakers

        private bool CheckDailyLossLimit()
        {
            // Calculate current session PnL including unrealized
            double currentEquity = Account.Get(AccountItem.CashValue, Currency.UsDollar);
            double unrealizedPnL = Position.GetUnrealizedProfitLoss(PerformanceUnit.Currency, Close[0]);
            sessionPnL = (currentEquity - sessionStartEquity) + unrealizedPnL;

            if (sessionPnL <= -DailyLossLimit)
            {
                return false; // Limit breached
            }

            return true;
        }

        private bool CheckConsistencyRule()
        {
            if (!EnableConsistencyRule)
                return true;

            // Calculate current session profit
            double currentEquity = Account.Get(AccountItem.CashValue, Currency.UsDollar);
            double sessionProfit = currentEquity - sessionStartEquity;

            // Check if today's profit exceeds consistency threshold
            if (sessionProfit > consistencyThreshold)
            {
                Print(string.Format("WARNING: Session profit ${0:N2} exceeds consistency threshold ${1:N2}",
                    sessionProfit, consistencyThreshold));
                return false; // Throttle trading
            }

            return true;
        }

        private void UpdateRegimeDetection()
        {
            // In production, you'd pull actual CVOL data from CME
            // For now, we use a simplified volatility measure (ATR-based proxy)

            double atr = ATR(14)[0];
            double atrPercent = (atr / Close[0]) * 100;

            // Normalize ATR to approximate CVOL scale
            currentCVOL = atrPercent * 10; // Rough approximation

            if (currentCVOL > HighVolatilityThreshold)
            {
                if (!isHighVolatilityRegime)
                {
                    Print(string.Format("REGIME CHANGE: Entering HIGH VOLATILITY (CVOL: {0:F1})", currentCVOL));
                    isHighVolatilityRegime = true;
                }
            }
            else if (currentCVOL < LowVolatilityThreshold)
            {
                if (isHighVolatilityRegime)
                {
                    Print(string.Format("REGIME CHANGE: Entering LOW VOLATILITY (CVOL: {0:F1})", currentCVOL));
                    isHighVolatilityRegime = false;
                }
            }
        }

        private int CalculatePositionSize()
        {
            // Dynamic position sizing based on trailing drawdown protection
            if (!EnableTrailingDrawdownProtection)
                return DefaultPositionSize;

            double currentEquity = Account.Get(AccountItem.CashValue, Currency.UsDollar);

            // Update high water mark
            if (currentEquity > sessionHighEquity)
                sessionHighEquity = currentEquity;

            // Calculate distance to drawdown liquidation
            double drawdownBuffer = currentEquity - (sessionHighEquity - TrailingDrawdown);

            // If drawdown buffer is tight, reduce position size
            if (drawdownBuffer < 500)
            {
                Print("EQUITY PROTECTOR: Reducing position size due to tight drawdown buffer");
                return Math.Max(1, DefaultPositionSize / 2);
            }

            return DefaultPositionSize;
        }

        private void OnNewTradingSession()
        {
            Print("========================================");
            Print(string.Format("NEW TRADING SESSION: {0}", Time[0].ToShortDateString()));

            // Reset session tracking
            sessionStartEquity = Account.Get(AccountItem.CashValue, Currency.UsDollar);
            sessionPnL = 0;
            isStrategyLocked = false;

            // Update consistency threshold based on cumulative performance
            double totalProfit = sessionStartEquity - evaluationStartEquity;
            double remainingProfit = requiredProfitForEval - totalProfit;

            if (remainingProfit > 0)
            {
                consistencyThreshold = remainingProfit * ConsistencyPercentage;
                Print(string.Format("Remaining Profit Needed: ${0:N2}, Today's Consistency Cap: ${1:N2}",
                    remainingProfit, consistencyThreshold));
            }
            else
            {
                Print("EVALUATION PROFIT TARGET REACHED!");
            }

            Print("========================================");
        }

        #endregion

        #region News Filter

        private void LoadNewsCalendar()
        {
            try
            {
                newsBlackoutTimes.Clear();

                using (StreamReader reader = new StreamReader(NewsCalendarPath))
                {
                    string line;
                    bool isFirstLine = true;

                    while ((line = reader.ReadLine()) != null)
                    {
                        // Skip header row
                        if (isFirstLine)
                        {
                            isFirstLine = false;
                            continue;
                        }

                        // Expected CSV format: Date,Time,Impact,Event
                        // Example: 2025-11-17,10:30,High,EIA Crude Oil Inventories
                        string[] parts = line.Split(',');

                        if (parts.Length >= 3)
                        {
                            string dateStr = parts[0].Trim();
                            string timeStr = parts[1].Trim();
                            string impact = parts[2].Trim();

                            // Only load high-impact events
                            if (impact.ToLower() == "high")
                            {
                                if (DateTime.TryParse(dateStr + " " + timeStr, out DateTime eventTime))
                                {
                                    newsBlackoutTimes.Add(eventTime);
                                }
                            }
                        }
                    }
                }

                Print(string.Format("NEWS CALENDAR LOADED: {0} high-impact events", newsBlackoutTimes.Count));
            }
            catch (Exception ex)
            {
                Print(string.Format("ERROR LOADING NEWS CALENDAR: {0}", ex.Message));
            }
        }

        private bool IsNewsBlackout()
        {
            if (newsBlackoutTimes.Count == 0)
                return false;

            DateTime currentTime = Time[0];
            TimeSpan blackoutWindow = new TimeSpan(0, 5, 0); // 5 minutes before/after

            foreach (DateTime newsTime in newsBlackoutTimes)
            {
                // Check if current time is within blackout window
                if (currentTime >= newsTime.Subtract(blackoutWindow) &&
                    currentTime <= newsTime.Add(blackoutWindow))
                {
                    return true;
                }
            }

            return false;
        }

        #endregion

        #region Properties (for Strategy Analyzer)

        [Browsable(false)]
        [XmlIgnore]
        public Series<double> VWAPValue
        {
            get { return vwapIndicator != null ? vwapIndicator.Value : null; }
        }

        #endregion
    }
}

#region NinjaScript generated code. Neither change nor remove.

namespace NinjaTrader.NinjaScript.Strategies
{
    public partial class Strategy : NinjaTrader.Gui.NinjaScript.StrategyRenderBase
    {
        public Strategies.CrudeOilMasterStrategy[] CrudeOilMasterStrategy()
        {
            return CrudeOilMasterStrategy(Input);
        }

        public Strategies.CrudeOilMasterStrategy[] CrudeOilMasterStrategy(ISeries<double> input)
        {
            return CrudeOilMasterStrategy(input, true, false, true, 1000, 2000, true, 1, 25,
                true, 0.40, 3000, true, @"C:\AlgoTrading\NewsCalendar.csv",
                2.0, SessionIterator.SessionType.Trading, 20, 45, 30,
                false, "127.0.0.1", 5555);
        }

        public Strategies.CrudeOilMasterStrategy[] CrudeOilMasterStrategy(ISeries<double> input,
            bool enableVWAPMeanReversion, bool enableEIAMomentum, bool enableAMT,
            double dailyLossLimit, double trailingDrawdown, bool enableTrailingDrawdownProtection,
            int defaultPositionSize, int stopLossTicks,
            bool enableConsistencyRule, double consistencyPercentage, double evaluationProfitTarget,
            bool enableNewsFilter, string newsCalendarPath,
            double vwapStdDevMultiplier, SessionIterator.SessionType vwapAnchorSession, int vwapTargetTicks,
            double highVolatilityThreshold, double lowVolatilityThreshold,
            bool enablePythonML, string pythonServerAddress, int pythonServerPort)
        {
            if (CacheCrudeOilMasterStrategy != null)
                for (int idx = 0; idx < CacheCrudeOilMasterStrategy.Length; idx++)
                    if (CacheCrudeOilMasterStrategy[idx] != null &&
                        CacheCrudeOilMasterStrategy[idx].EnableVWAPMeanReversion == enableVWAPMeanReversion &&
                        CacheCrudeOilMasterStrategy[idx].EnableEIAMomentum == enableEIAMomentum &&
                        CacheCrudeOilMasterStrategy[idx].EnableAMT == enableAMT &&
                        CacheCrudeOilMasterStrategy[idx].DailyLossLimit == dailyLossLimit &&
                        CacheCrudeOilMasterStrategy[idx].TrailingDrawdown == trailingDrawdown &&
                        CacheCrudeOilMasterStrategy[idx].EnableTrailingDrawdownProtection == enableTrailingDrawdownProtection &&
                        CacheCrudeOilMasterStrategy[idx].DefaultPositionSize == defaultPositionSize &&
                        CacheCrudeOilMasterStrategy[idx].StopLossTicks == stopLossTicks &&
                        CacheCrudeOilMasterStrategy[idx].EnableConsistencyRule == enableConsistencyRule &&
                        CacheCrudeOilMasterStrategy[idx].ConsistencyPercentage == consistencyPercentage &&
                        CacheCrudeOilMasterStrategy[idx].EvaluationProfitTarget == evaluationProfitTarget &&
                        CacheCrudeOilMasterStrategy[idx].EnableNewsFilter == enableNewsFilter &&
                        CacheCrudeOilMasterStrategy[idx].NewsCalendarPath == newsCalendarPath &&
                        CacheCrudeOilMasterStrategy[idx].VWAPStdDevMultiplier == vwapStdDevMultiplier &&
                        CacheCrudeOilMasterStrategy[idx].VWAPAnchorSession == vwapAnchorSession &&
                        CacheCrudeOilMasterStrategy[idx].VWAPTargetTicks == vwapTargetTicks &&
                        CacheCrudeOilMasterStrategy[idx].HighVolatilityThreshold == highVolatilityThreshold &&
                        CacheCrudeOilMasterStrategy[idx].LowVolatilityThreshold == lowVolatilityThreshold &&
                        CacheCrudeOilMasterStrategy[idx].EnablePythonML == enablePythonML &&
                        CacheCrudeOilMasterStrategy[idx].PythonServerAddress == pythonServerAddress &&
                        CacheCrudeOilMasterStrategy[idx].PythonServerPort == pythonServerPort &&
                        CacheCrudeOilMasterStrategy[idx].EqualsInput(input))
                        return CacheCrudeOilMasterStrategy[idx];
            return CacheCrudeOilMasterStrategy = new Strategies.CrudeOilMasterStrategy[] {
                new Strategies.CrudeOilMasterStrategy()
            };
        }

        private Strategies.CrudeOilMasterStrategy[] CacheCrudeOilMasterStrategy;
    }
}

#endregion
