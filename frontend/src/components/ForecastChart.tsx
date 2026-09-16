import { useMemo } from 'react';
import ReactECharts from 'echarts-for-react';

interface ForecastData {
  symbol: string;
  historical: number[];
  point_forecast: number[];
  quantiles: {
    q10: number[];
    q90: number[];
  };
}

const ForecastChart = ({ data }: { data: ForecastData }) => {
  const options = useMemo(() => {
    // Generate synthetic X-axis data (indices)
    const histLen = data.historical.length;
    const foreLen = data.point_forecast.length;
    const xAxisData = Array.from({ length: histLen + foreLen }, (_, i) => i);

    // Pad forecast data with nulls so it starts after historical data
    const paddedPoint = [...Array(histLen).fill(null), ...data.point_forecast];
    const paddedQ10 = [...Array(histLen).fill(null), ...data.quantiles.q10];
    const paddedQ90 = [...Array(histLen).fill(null), ...data.quantiles.q90];

    return {
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'cross' }
      },
      legend: {
        data: ['Historical', 'Point Forecast', 'Q10-Q90 Interval']
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: xAxisData
      },
      yAxis: {
        type: 'value',
        scale: true
      },
      series: [
        {
          name: 'Historical',
          type: 'line',
          data: data.historical,
          itemStyle: { color: '#4B5563' },
          lineStyle: { width: 2 },
          showSymbol: false,
        },
        {
          name: 'Point Forecast',
          type: 'line',
          data: paddedPoint,
          itemStyle: { color: '#2563EB' },
          lineStyle: { width: 2, type: 'dashed' },
          showSymbol: true,
        },
        {
          name: 'Q10-Q90 Interval',
          type: 'line',
          data: paddedQ90,
          lineStyle: { opacity: 0 },
          showSymbol: false,
          areaStyle: {
            color: '#93C5FD',
            opacity: 0.3
          }
        },
        {
          name: 'Q10-Q90 Interval (Lower)',
          type: 'line',
          data: paddedQ10,
          lineStyle: { opacity: 0 },
          showSymbol: false,
          areaStyle: {
            color: '#fff',
            opacity: 1
          },
          // ECharts trick: fill the area up to q10 with white to make a band
          // (Actually in modern echarts we can use stack or markArea. This is a simple visual hack for now)
        }
      ]
    };
  }, [data]);

  return (
    <ReactECharts
      option={options}
      style={{ height: '100%', width: '100%', minHeight: '400px' }}
      notMerge={true}
      lazyUpdate={true}
    />
  );
};

export default ForecastChart;
