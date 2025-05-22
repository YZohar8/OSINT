import React from 'react';
import { render, screen } from '@testing-library/react';
import ResponseCard from './ResponseCard';

describe('ResponseCard', () => {
  it('renders domain and status', () => {
    render(<ResponseCard 
      domain="example.com" 
      response={{ info: "Test response" }} 
      status="completed" 
      createdAt="2024-01-01T00:00:00Z" 
      completedAt="2024-01-01T01:00:00Z"
    />);
    
    expect(screen.getByText(/example.com/i)).toBeInTheDocument();
    expect(screen.getByText(/Status: completed/i)).toBeInTheDocument();
    expect(screen.getByText(/Completed:/i)).toBeInTheDocument();
    expect(screen.getByText(/"info": "Test response"/i)).toBeInTheDocument();
  });
});
