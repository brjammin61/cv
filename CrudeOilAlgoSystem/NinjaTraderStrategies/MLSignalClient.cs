/*
 * ML Signal Client for NinjaTrader 8
 *
 * NetMQ (ZeroMQ) client for communicating with Python ML server
 *
 * Requirements:
 * - Install NetMQ via NuGet: Install-Package NetMQ
 * - Ensure NetMQ.dll is compatible with .NET Framework 4.8
 *
 * Author: Algorithmic Trading Framework 2025
 */

using System;
using System.Collections.Generic;
using System.Text;
using NetMQ;
using NetMQ.Sockets;
using Newtonsoft.Json;
using NinjaTrader.NinjaScript;

namespace NinjaTrader.NinjaScript.Strategies
{
    /// <summary>
    /// Client for communicating with Python ML signal server via ZeroMQ
    /// </summary>
    public class MLSignalClient : IDisposable
    {
        private RequestSocket client;
        private string serverAddress;
        private int timeout;
        private bool isConnected;

        /// <summary>
        /// Initialize ML signal client
        /// </summary>
        /// <param name="host">Server host (default: 127.0.0.1)</param>
        /// <param name="port">Server port (default: 5555)</param>
        /// <param name="timeoutMs">Request timeout in milliseconds (default: 5000)</param>
        public MLSignalClient(string host = "127.0.0.1", int port = 5555, int timeoutMs = 5000)
        {
            this.serverAddress = $"tcp://{host}:{port}";
            this.timeout = timeoutMs;
            this.isConnected = false;

            try
            {
                Connect();
            }
            catch (Exception ex)
            {
                NinjaTrader.Code.Output.Process(
                    $"ML Client Error: Failed to connect to {serverAddress} - {ex.Message}",
                    NinjaTrader.Cbi.PrintTo.OutputTab1
                );
            }
        }

        /// <summary>
        /// Connect to the Python ML server
        /// </summary>
        private void Connect()
        {
            if (isConnected)
                return;

            try
            {
                client = new RequestSocket();
                client.Connect(serverAddress);
                client.Options.Linger = TimeSpan.FromMilliseconds(1000);

                isConnected = true;

                NinjaTrader.Code.Output.Process(
                    $"ML Client: Connected to {serverAddress}",
                    NinjaTrader.Cbi.PrintTo.OutputTab1
                );
            }
            catch (Exception ex)
            {
                isConnected = false;
                throw new Exception($"Failed to connect to ML server: {ex.Message}");
            }
        }

        /// <summary>
        /// Request trading signal from ML server
        /// </summary>
        /// <param name="bars">List of OHLCV bar data</param>
        /// <returns>ML signal response</returns>
        public MLSignalResponse GetTradingSignal(List<OHLCVBar> bars)
        {
            if (!isConnected)
            {
                return new MLSignalResponse
                {
                    Status = "error",
                    Message = "Not connected to ML server",
                    Signal = 0,
                    Confidence = 0
                };
            }

            try
            {
                // Construct request
                var request = new
                {
                    request_type = "signal",
                    timestamp = DateTime.Now.ToString("o"),
                    bars = bars
                };

                string jsonRequest = JsonConvert.SerializeObject(request);

                // Send request
                client.SendFrame(jsonRequest);

                // Wait for response with timeout
                string jsonResponse;
                bool received = client.TryReceiveFrameString(TimeSpan.FromMilliseconds(timeout), out jsonResponse);

                if (!received)
                {
                    return new MLSignalResponse
                    {
                        Status = "error",
                        Message = "Request timeout",
                        Signal = 0,
                        Confidence = 0
                    };
                }

                // Parse response
                MLSignalResponse response = JsonConvert.DeserializeObject<MLSignalResponse>(jsonResponse);
                return response;
            }
            catch (Exception ex)
            {
                return new MLSignalResponse
                {
                    Status = "error",
                    Message = $"Request failed: {ex.Message}",
                    Signal = 0,
                    Confidence = 0
                };
            }
        }

        /// <summary>
        /// Request volatility prediction from ML server
        /// </summary>
        /// <param name="bars">List of OHLCV bar data</param>
        /// <returns>Volatility prediction response</returns>
        public MLVolatilityResponse GetVolatilityPrediction(List<OHLCVBar> bars)
        {
            if (!isConnected)
            {
                return new MLVolatilityResponse
                {
                    Status = "error",
                    Message = "Not connected to ML server",
                    VolatilityRegime = "unknown"
                };
            }

            try
            {
                // Construct request
                var request = new
                {
                    request_type = "predict_volatility",
                    timestamp = DateTime.Now.ToString("o"),
                    bars = bars
                };

                string jsonRequest = JsonConvert.SerializeObject(request);

                // Send request
                client.SendFrame(jsonRequest);

                // Wait for response
                string jsonResponse;
                bool received = client.TryReceiveFrameString(TimeSpan.FromMilliseconds(timeout), out jsonResponse);

                if (!received)
                {
                    return new MLVolatilityResponse
                    {
                        Status = "error",
                        Message = "Request timeout",
                        VolatilityRegime = "unknown"
                    };
                }

                // Parse response
                MLVolatilityResponse response = JsonConvert.DeserializeObject<MLVolatilityResponse>(jsonResponse);
                return response;
            }
            catch (Exception ex)
            {
                return new MLVolatilityResponse
                {
                    Status = "error",
                    Message = $"Request failed: {ex.Message}",
                    VolatilityRegime = "unknown"
                };
            }
        }

        /// <summary>
        /// Check if ML server is healthy
        /// </summary>
        /// <returns>True if server responds to health check</returns>
        public bool HealthCheck()
        {
            if (!isConnected)
                return false;

            try
            {
                var request = new { request_type = "health_check" };
                string jsonRequest = JsonConvert.SerializeObject(request);

                client.SendFrame(jsonRequest);

                string jsonResponse;
                bool received = client.TryReceiveFrameString(TimeSpan.FromMilliseconds(2000), out jsonResponse);

                if (received)
                {
                    var response = JsonConvert.DeserializeObject<Dictionary<string, string>>(jsonResponse);
                    return response.ContainsKey("status") && response["status"] == "healthy";
                }

                return false;
            }
            catch
            {
                return false;
            }
        }

        /// <summary>
        /// Disconnect from ML server
        /// </summary>
        public void Disconnect()
        {
            if (client != null)
            {
                client.Disconnect(serverAddress);
                client.Dispose();
                client = null;
                isConnected = false;

                NinjaTrader.Code.Output.Process(
                    "ML Client: Disconnected from server",
                    NinjaTrader.Cbi.PrintTo.OutputTab1
                );
            }
        }

        /// <summary>
        /// Dispose of resources
        /// </summary>
        public void Dispose()
        {
            Disconnect();
        }
    }

    /// <summary>
    /// OHLCV bar data structure for ML requests
    /// </summary>
    public class OHLCVBar
    {
        [JsonProperty("open")]
        public double Open { get; set; }

        [JsonProperty("high")]
        public double High { get; set; }

        [JsonProperty("low")]
        public double Low { get; set; }

        [JsonProperty("close")]
        public double Close { get; set; }

        [JsonProperty("volume")]
        public long Volume { get; set; }
    }

    /// <summary>
    /// ML signal response from Python server
    /// </summary>
    public class MLSignalResponse
    {
        [JsonProperty("status")]
        public string Status { get; set; }

        [JsonProperty("signal")]
        public int Signal { get; set; }  // -1 = Short, 0 = Neutral, 1 = Long

        [JsonProperty("confidence")]
        public double Confidence { get; set; }

        [JsonProperty("volatility_prediction")]
        public string VolatilityPrediction { get; set; }

        [JsonProperty("timestamp")]
        public string Timestamp { get; set; }

        [JsonProperty("message")]
        public string Message { get; set; }
    }

    /// <summary>
    /// ML volatility prediction response
    /// </summary>
    public class MLVolatilityResponse
    {
        [JsonProperty("status")]
        public string Status { get; set; }

        [JsonProperty("volatility_regime")]
        public string VolatilityRegime { get; set; }  // "low", "medium", "high"

        [JsonProperty("timestamp")]
        public string Timestamp { get; set; }

        [JsonProperty("message")]
        public string Message { get; set; }
    }
}
