import { useEffect, useRef } from 'react';
import { resolveBackendUrl } from '@/services/runtime';

type HeatmapPoint = {
  name: string;
  value: number;
};

declare global {
  interface Window {
    echarts?: any;
  }
}

let chinaMapRegistered = false;

async function ensureChinaMapRegistered(echarts: any) {
  if (chinaMapRegistered) {
    return;
  }

  window.echarts = echarts;
  try {
    const response = await fetch('/china.js');
    if (!response.ok) {
        throw new Error(`Failed to fetch china.js: ${response.statusText}`);
    }
    const script = await response.text();
    new Function('window', 'globalThis', 'self', script)(window, window, window);
    chinaMapRegistered = true;
  } catch (err) {
    console.error("加载中国地图资源失败: ", err);
    // 即使失败，也可静默处理，仅仅图表会无法渲染边界
  }
}

export function ChinaHeatmap({ data, height = 300 }: { data: HeatmapPoint[]; height?: number }) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<any>(null);

  useEffect(() => {
    let mounted = true;

    const boot = async () => {
      if (!containerRef.current) {
        return;
      }

      const echarts = await import('echarts');
      await ensureChinaMapRegistered(echarts);
      if (!mounted || !containerRef.current) {
        return;
      }

      const chart = echarts.init(containerRef.current);
      chartRef.current = chart;

      chart.setOption({
        backgroundColor: 'transparent',
        tooltip: {
          trigger: 'item',
          formatter: (params: any) => `${params.name}<br/>热力值：${params.value ?? 0}`,
        },
        visualMap: {
          min: 0,
          max: Math.max(...data.map((item) => item.value), 10),
          left: 'left',
          bottom: 10,
          text: ['高', '低'],
          calculable: true,
          itemWidth: 12,
          textStyle: {
            color: '#333333',
          },
          inRange: {
            color: ['#e6f7ff', '#1890ff'],
          },
        },
        series: [
          {
            name: '舆情热力',
            type: 'map',
            map: 'china',
            roam: true,
            label: {
              show: true,
              fontSize: 10,
              color: '#333',
            },
            emphasis: {
              label: {
                color: '#fff',
              },
              itemStyle: {
                areaColor: '#40a9ff',
              },
            },
            itemStyle: {
              areaColor: '#f0f2f5',
              borderColor: '#d9d9d9',
            },
            data,
          },
        ],
      });

      const handleResize = () => chart.resize();
      window.addEventListener('resize', handleResize);

      return () => {
        window.removeEventListener('resize', handleResize);
      };
    };

    let cleanup: (() => void) | undefined;
    void boot().then((dispose) => {
      cleanup = dispose;
    });

    return () => {
      mounted = false;
      cleanup?.();
      chartRef.current?.dispose();
      chartRef.current = null;
    };
  }, []);

  useEffect(() => {
    if (!chartRef.current) {
      return;
    }
    chartRef.current.setOption({
      visualMap: {
        max: Math.max(...data.map((item) => item.value), 10),
      },
      series: [{ data }],
    });
  }, [data]);

  return <div ref={containerRef} style={{ width: '100%', height }} />;
}
