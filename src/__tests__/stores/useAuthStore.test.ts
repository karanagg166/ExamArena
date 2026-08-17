import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useAuthStore } from '@/stores/useAuthStore';
import { api } from '@/lib/axios';
import type { User } from '@/types';

vi.mock('@/lib/axios', () => ({
  api: {
    post: vi.fn(),
    get: vi.fn(),
  },
}));

const mockFullUser: User = {
  id: 'usr_1',
  email: 'test@examarena.com',
  name: 'Test User',
  role: 'STUDENT' as const,
  phoneNo: '+919876543210',
  city: 'Mumbai',
  state: 'Maharashtra',
  country: 'India',
  pincode: '400001',
  dateOfBirth: '2000-01-01T00:00:00Z',
  createdAt: '2026-01-01T00:00:00Z',
  updatedAt: '2026-01-01T00:00:00Z',
};

describe('Unit: useAuthStore', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useAuthStore.setState({ user: null, loading: false, error: null });
  });

  it('login success sets user state and clears error', async () => {
    vi.mocked(api.post).mockResolvedValueOnce({ data: {} });
    vi.mocked(api.get).mockResolvedValueOnce({ data: mockFullUser });

    await useAuthStore.getState().login('test@examarena.com', 'Pass123!');

    expect(api.post).toHaveBeenCalledWith('/api/v1/auth/login', {
      email: 'test@examarena.com',
      password: 'Pass123!',
    });
    expect(useAuthStore.getState().user).toEqual(mockFullUser);
    expect(useAuthStore.getState().error).toBeNull();
    expect(useAuthStore.getState().loading).toBe(false);
  });

  it('login failure sets error message', async () => {
    vi.mocked(api.post).mockRejectedValueOnce(new Error('Invalid email or password'));

    await useAuthStore.getState().login('test@examarena.com', 'WrongPass');

    expect(useAuthStore.getState().user).toBeNull();
    expect(useAuthStore.getState().error).toBe('Invalid email or password');
    expect(useAuthStore.getState().loading).toBe(false);
  });

  it('logout success clears user state', async () => {
    useAuthStore.setState({
      user: mockFullUser,
    });
    vi.mocked(api.post).mockResolvedValueOnce({ data: {} });

    await useAuthStore.getState().logout();

    expect(api.post).toHaveBeenCalledWith('/api/v1/auth/logout');
    expect(useAuthStore.getState().user).toBeNull();
    expect(useAuthStore.getState().loading).toBe(false);
  });

  it('fetchMe retrieves authenticated user profile', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({ data: mockFullUser });

    await useAuthStore.getState().fetchMe();

    expect(api.get).toHaveBeenCalledWith('/api/v1/auth/me');
    expect(useAuthStore.getState().user).toEqual(mockFullUser);
    expect(useAuthStore.getState().error).toBeNull();
  });
});
