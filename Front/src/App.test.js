import { render, screen, fireEvent } from '@testing-library/react';
import App from './App';

test('renders title and input', () => {
  render(<App />);
  expect(screen.getByText(/OSINT Scanner/i)).toBeInTheDocument();
  expect(screen.getByPlaceholderText(/Enter domain/i)).toBeInTheDocument();
});

test('submits domain and resets input', async () => {
  global.fetch = jest.fn(() =>
    Promise.resolve({
      json: () => Promise.resolve({ message: 'Scan started for test.com' })
    })
  );

  render(<App />);
  const input = screen.getByPlaceholderText(/Enter domain/i);
  fireEvent.change(input, { target: { value: 'test.com' } });
  fireEvent.click(screen.getByText(/Scan/i));

  expect(await screen.findByText(/Scan started for test.com/i)).toBeInTheDocument();
  expect(input.value).toBe('');
});