import '@testing-library/jest-dom'
import { render, screen, fireEvent } from '@testing-library/react'
import Home from '../page'
import { useRouter } from 'next/navigation'

// Mock the useRouter hook
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
}))

// Mock the global fetch
global.fetch = jest.fn(() =>
  Promise.resolve({
    json: () => Promise.resolve({
      playersTracked: 1,
      battlesAnalyzed: "5.0K",
      avgWinRate: "50.0%",
      status: "ONLINE"
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

  it('renders the search input', () => {
    render(<Home />)
    expect(screen.getByPlaceholderText('ENTER PLAYER HANDLE...')).toBeInTheDocument()
  })

  it('calls router.push when a player name is submitted', () => {
    render(<Home />)
    const input = screen.getByPlaceholderText('ENTER PLAYER HANDLE...')
    const submitButton = screen.getByText('INITIALIZE')

    fireEvent.change(input, { target: { value: 'TestPlayer' } })
    fireEvent.click(submitButton)

    expect(mockPush).toHaveBeenCalledWith('/player/TestPlayer')
  })
})
