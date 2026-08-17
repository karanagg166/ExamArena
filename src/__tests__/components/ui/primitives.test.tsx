import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Button } from '@/components/ui/button';
import { EmptyState } from '@/components/ui/empty-state';
import { IndiaStateCitySelect } from '@/components/ui/IndiaStateCitySelect';

describe('Component: UI Primitives (C29-C33)', () => {
  describe('Button', () => {
    it('C29: renders button with text', () => {
      render(<Button>Submit Form</Button>);
      expect(screen.getByRole('button', { name: /submit form/i })).toBeInTheDocument();
    });

    it('C30: respects disabled state and does not trigger onClick', async () => {
      const user = userEvent.setup();
      const handleClick = vi.fn();
      render(<Button disabled onClick={handleClick}>Disabled Button</Button>);

      const btn = screen.getByRole('button', { name: /disabled button/i });
      expect(btn).toBeDisabled();

      await user.click(btn);
      expect(handleClick).not.toHaveBeenCalled();
    });

    it('applies variant classes correctly', () => {
      const { container } = render(<Button variant="destructive">Delete</Button>);
      expect(container.firstChild).toHaveClass('text-destructive');
    });
  });

  describe('EmptyState', () => {
    it('C31: renders title, description, and action element', () => {
      render(
        <EmptyState
          title="No exams found"
          description="Create your first exam to get started"
          action={<Button>Create Exam</Button>}
        />
      );

      expect(screen.getByText('No exams found')).toBeInTheDocument();
      expect(screen.getByText('Create your first exam to get started')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /create exam/i })).toBeInTheDocument();
    });
  });

  describe('IndiaStateCitySelect', () => {
    it('C33: renders states and calls onStateChange when selected', () => {
      const handleStateChange = vi.fn();
      const handleCityChange = vi.fn();

      render(
        <IndiaStateCitySelect
          selectedState=""
          selectedCity=""
          onStateChange={handleStateChange}
          onCityChange={handleCityChange}
        />
      );

      const stateSelect = screen.getByLabelText(/state/i);
      expect(stateSelect).toBeInTheDocument();

      fireEvent.change(stateSelect, { target: { value: 'Maharashtra' } });
      expect(handleStateChange).toHaveBeenCalledWith('Maharashtra');
    });

    it('renders city dropdown when state is selected', () => {
      const handleStateChange = vi.fn();
      const handleCityChange = vi.fn();

      render(
        <IndiaStateCitySelect
          selectedState="Maharashtra"
          selectedCity=""
          onStateChange={handleStateChange}
          onCityChange={handleCityChange}
        />
      );

      const citySelect = screen.getByLabelText(/city/i);
      expect(citySelect).toBeInTheDocument();
      expect(screen.getByText('Mumbai')).toBeInTheDocument();
      expect(screen.getByText('Pune')).toBeInTheDocument();

      fireEvent.change(citySelect, { target: { value: 'Mumbai' } });
      expect(handleCityChange).toHaveBeenCalledWith('Mumbai');
    });

    it('renders error messages when provided', () => {
      render(
        <IndiaStateCitySelect
          selectedState=""
          selectedCity=""
          onStateChange={vi.fn()}
          onCityChange={vi.fn()}
          stateError="State is required"
          cityError="City is required"
        />
      );

      expect(screen.getByText('State is required')).toBeInTheDocument();
      expect(screen.getByText('City is required')).toBeInTheDocument();
    });
  });
});
