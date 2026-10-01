import '@testing-library/jest-dom'
import { render, screen } from '@testing-library/react'
import { BattlesChart, WinRateChart, AvgDamageChart } from '../charts'

// Mock the Recharts components so they don't break in jsdom
jest.mock('recharts', () => {
  const OriginalModule = jest.requireActual('recharts')
  return {
    ...OriginalModule,
    ResponsiveContainer: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
    AreaChart: () => <div data-testid="area-chart" />,
    BarChart: () => <div data-testid="bar-chart" />,
  }
})

describe('Chart Components', () => {
  const mockHistory = [
    { date: '2023-01-01', battles: 100, winRate: 50.0, avgDamage: 40000 },
    { date: '2023-01-02', battles: 110, winRate: 51.5, avgDamage: 45000 },
  ]

  it('renders BattlesChart correctly', () => {
    render(<BattlesChart data={mockHistory} />)
    expect(screen.getByTestId('bar-chart')).toBeInTheDocument()
  })

  it('renders WinRateChart correctly', () => {
    render(<WinRateChart data={mockHistory} />)
    expect(screen.getByTestId('area-chart')).toBeInTheDocument()
  })

  it('renders AvgDamageChart correctly', () => {
    render(<AvgDamageChart data={mockHistory} />)
    expect(screen.getByTestId('area-chart')).toBeInTheDocument()
  })
})
