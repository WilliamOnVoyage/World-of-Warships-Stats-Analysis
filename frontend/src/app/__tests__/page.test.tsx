import '@testing-library/jest-dom'
import { render, screen, fireEvent } from '@testing-library/react'
import Home from '../page'
import { useRouter } from 'next/navigation'

jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
}))

global.fetch = jest.fn(() =>
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve({
      totalPlayers: 3268909,
      totalBattles: 18400000,
      avgWinRate: 49.12,
      status: "online"
    }),
  })
) as jest.Mock

describe('Home Page', () => {
  const mockPush = jest.fn()
  
  beforeEach(() => {
    (useRouter as jest.Mock).mockReturnValue({
      push: mockPush,
    })
    jest.clearAllMocks()
  })

  it('renders the commander search input', () => {
    render(<Home />)
    expect(screen.getByPlaceholderText(/ENTER COMMANDER HANDLE/i)).toBeInTheDocument()
  })

  it('calls router.push when a commander name is submitted', () => {
    render(<Home />)
    const input = screen.getByPlaceholderText(/ENTER COMMANDER HANDLE/i)
    const submitButton = screen.getByText(/DISPATCH QUERY/i)

    fireEvent.change(input, { target: { value: 'TestPlayer' } })
    fireEvent.click(submitButton)

    expect(mockPush).toHaveBeenCalledWith('/player/TestPlayer')
  })
})
