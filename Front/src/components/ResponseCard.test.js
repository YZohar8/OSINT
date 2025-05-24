import React from 'react';
import { render, screen } from '@testing-library/react';
import ResponseCard from './ResponseCard';

describe('ResponseCard', () => {
  it('renders domain, status, dates and response JSON', () => {
    const response = [{ domain: "example.com", result: { info: "Test response" } }];
    const createdAt = "2024-01-01T00:00:00Z";
    const completedAt = "2024-01-01T01:00:00Z";

    render(
      <ResponseCard 
        domain="example.com" 
        response={response} 
        status="completed" 
        createdAt={createdAt} 
        completedAt={completedAt}
      />
    );

    // Find the domain in the heading specifically (avoid the JSON <pre>)
    const domainHeading = screen.getByRole('heading', { level: 3, name: /example.com/i });
    expect(domainHeading).toBeInTheDocument();

    // Check status text
    expect(screen.getByText(/Status: completed/i)).toBeInTheDocument();

    // Check dates with local formatting
    expect(screen.getByText(new RegExp(new Date(createdAt).toLocaleString()))).toBeInTheDocument();
    expect(screen.getByText(new RegExp(new Date(completedAt).toLocaleString()))).toBeInTheDocument();

    // Check part of JSON content (inside the <pre>)
    expect(screen.getByText(/"domain": "example.com"/i)).toBeInTheDocument();
    expect(screen.getByText(/"info": "Test response"/i)).toBeInTheDocument();
  });
});
