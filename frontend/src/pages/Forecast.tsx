import { useState } from 'react'
import ForecastChart from '../components/ForecastChart'

const Forecast = () => {
  const [symbol, setSymbol] = useState('RELIANCE.NS')
  const [horizon, setHorizon] = useState(5)
  const [contextLength, setContextLength] = useState(512)
  const [model, setModel] = useState('timesfm3')
  const [targetMode, setTargetMode] = useState('raw_price')

  // Mock data for initial rendering. In a real scenario, this comes from React Query via API
  const [forecastData, setForecastData] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(false)

  const handleRunForecast = () => {
    setIsLoading(true)
    // Simulate API call
    setTimeout(() => {
      setForecastData({
        symbol,
        point_forecast: [2550, 2565, 2560, 2580, 2595],
        historical: Array.from({length: 50}, (_, i) => 2400 + i * 3 + Math.random() * 20),
        quantiles: {
          q10: [2530, 2540, 2530, 2545, 2550],
          q90: [2570, 2590, 2590, 2615, 2640]
        }
      })
      setIsLoading(false)
    }, 1500)
  }

  return (
    <div className="flex h-full flex-col md:flex-row bg-gray-50">
      {/* Left Panel: Controls */}
      <div className="w-full md:w-80 bg-white shadow-sm border-r p-6 flex flex-col space-y-6 overflow-y-auto">
        <div>
          <h2 className="text-lg font-semibold text-gray-800 mb-4">Configuration</h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Symbol</label>
              <input 
                type="text" 
                value={symbol}
                onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                className="w-full px-3 py-2 border rounded-md focus:ring-blue-500 focus:border-blue-500"
                placeholder="e.g. RELIANCE.NS"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Target Mode</label>
              <select 
                value={targetMode}
                onChange={(e) => setTargetMode(e.target.value)}
                className="w-full px-3 py-2 border rounded-md focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="raw_price">Raw Price</option>
                <option value="log_return">Log Return</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Model Provider</label>
              <select 
                value={model}
                onChange={(e) => setModel(e.target.value)}
                className="w-full px-3 py-2 border rounded-md focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="timesfm3">TimesFM 3.0 (GPU)</option>
                <option value="timesfm25">TimesFM 2.5</option>
                <option value="naive">Naive Baseline</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Context Length: {contextLength}
              </label>
              <input 
                type="range" 
                min="32" max="4096" step="32"
                value={contextLength}
                onChange={(e) => setContextLength(parseInt(e.target.value))}
                className="w-full"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Forecast Horizon: {horizon}
              </label>
              <input 
                type="range" 
                min="1" max="128" step="1"
                value={horizon}
                onChange={(e) => setHorizon(parseInt(e.target.value))}
                className="w-full"
              />
            </div>
          </div>
        </div>

        <button 
          onClick={handleRunForecast}
          disabled={isLoading}
          className={`w-full py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white ${isLoading ? 'bg-blue-400' : 'bg-blue-600 hover:bg-blue-700'} focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors`}
        >
          {isLoading ? 'Running...' : 'Run Forecast'}
        </button>
      </div>

      {/* Center/Right Panel: Chart and Data */}
      <div className="flex-1 flex flex-col p-6 overflow-y-auto">
        <div className="bg-white p-6 rounded-lg shadow-sm border mb-6 flex-1 min-h-[400px]">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">
            Forecast Visualization {forecastData ? `(${forecastData.symbol})` : ''}
          </h3>
          
          {forecastData ? (
            <ForecastChart data={forecastData} />
          ) : (
            <div className="h-full flex items-center justify-center text-gray-400 border-2 border-dashed rounded-lg">
              Configure parameters and run forecast to view results
            </div>
          )}
        </div>

        {/* Disclaimer */}
        <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 rounded-r-md text-sm text-yellow-800 mt-auto">
          <p className="font-bold mb-1">Research Disclaimer</p>
          <p>Forecasts generated by this tool are for research and educational purposes only. They do not constitute financial advice. Time-series foundation models are experimental and can produce highly inaccurate predictions in volatile markets.</p>
        </div>
      </div>
    </div>
  )
}

export default Forecast
