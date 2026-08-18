import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ChangePasswordForm } from '@/components/profile/ChangePasswordForm';
import { api } from '@/lib/axios';

vi.mock('@/lib/axios', () => ({
  api: {
    post: vi.fn(),
  },
}));

describe('Component: ChangePasswordForm (C27-C28)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('C27: renders all password fields and submit button', () => {
    render(<ChangePasswordForm />);
    expect(screen.getByLabelText(/current password/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^new password/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/confirm new password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /update password/i })).toBeInTheDocument();
  });

  it('C28: shows error when new passwords do not match', async () => {
    const user = userEvent.setup();
    render(<ChangePasswordForm />);

    await user.type(screen.getByLabelText(/current password/i), 'CurrentPass123!');
    await user.type(screen.getByLabelText(/^new password/i), 'NewPass123!');
    await user.type(screen.getByLabelText(/confirm new password/i), 'DifferentPass123!');

    await user.click(screen.getByRole('button', { name: /update password/i }));

    expect(screen.getByText(/new passwords do not match/i)).toBeInTheDocument();
    expect(api.post).not.toHaveBeenCalled();
  });

  it('shows error when new password is too short (<6 chars)', async () => {
    const user = userEvent.setup();
    render(<ChangePasswordForm />);

    await user.type(screen.getByLabelText(/current password/i), 'CurrentPass123!');
    await user.type(screen.getByLabelText(/^new password/i), '12345');
    await user.type(screen.getByLabelText(/confirm new password/i), '12345');

    await user.click(screen.getByRole('button', { name: /update password/i }));

    expect(screen.getByText(/at least 6 characters/i)).toBeInTheDocument();
    expect(api.post).not.toHaveBeenCalled();
  }, 10000);

  it('calls api.post on valid input and shows success message', async () => {
    const user = userEvent.setup();
    vi.mocked(api.post).mockResolvedValueOnce({ data: { message: 'Password changed successfully' } });

    render(<ChangePasswordForm />);

    await user.type(screen.getByLabelText(/current password/i), 'OldPass123!');
    await user.type(screen.getByLabelText(/^new password/i), 'NewSecret123!');
    await user.type(screen.getByLabelText(/confirm new password/i), 'NewSecret123!');

    await user.click(screen.getByRole('button', { name: /update password/i }));

    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith('/api/v1/auth/change-password', {
        currentPassword: 'OldPass123!',
        newPassword: 'NewSecret123!',
      });
      expect(screen.getByText(/password changed successfully/i)).toBeInTheDocument();
    });
  }, 10000);
});
