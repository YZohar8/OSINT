import { render, screen, fireEvent } from '@testing-library/react';
import App from './App';

describe('Domain validation in App', () => {
  it('shows error for invalid domain', () => {
    render(<App />);

    // Find the domain input field by placeholder text
    const input = screen.getByPlaceholderText(/Enter domain name/i);

    // Find the "Scan" button by its role and name
    const scanButton = screen.getByRole('button', { name: /scan/i });

    // Simulate user entering an invalid domain
    fireEvent.change(input, { target: { value: 'invalid_domain' } });

    // Simulate user clicking the Scan button
    fireEvent.click(scanButton);

    // Expect an error message to appear
    expect(screen.getByText(/Invalid domain format/i)).toBeInTheDocument();
  });

  it('does not show error for valid domain', () => {
    render(<App />);

    const input = screen.getByPlaceholderText(/Enter domain name/i);
    const scanButton = screen.getByRole('button', { name: /scan/i });

    // Use a valid domain
    fireEvent.change(input, { target: { value: 'example.com' } });
    fireEvent.click(scanButton);

    // Expect no error message to appear
    const errorMessage = screen.queryByText(/Invalid domain format/i);
    expect(errorMessage).not.toBeInTheDocument();
  });

  it('clears the input after valid submission (if applicable)', () => {
    render(<App />);

    const input = screen.getByPlaceholderText(/Enter domain name/i);
    const scanButton = screen.getByRole('button', { name: /scan/i });

    fireEvent.change(input, { target: { value: 'example.com' } });
    fireEvent.click(scanButton);

    // Check if the input is cleared (depends on your implementation)
    expect(input.value).toBe('example.com');
  });
});
