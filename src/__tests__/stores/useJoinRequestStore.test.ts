import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useJoinRequestStore } from '@/stores/useJoinRequestStore';
import { api } from '@/lib/axios';
import type { ClassJoinRequest } from '@/types';

vi.mock('@/lib/axios', () => ({
  api: {
    post: vi.fn(),
    get: vi.fn(),
    patch: vi.fn(),
  },
}));

function makeMockRequest(id: string, classId: string, status: 'PENDING' | 'APPROVED' | 'REJECTED'): ClassJoinRequest {
  return {
    id,
    classId,
    className: 'Class 10-A',
    studentName: 'Student 1',
    studentEmail: 'student1@examarena.com',
    status,
    studentUserId: 'usr_student',
    requestedAt: '2026-01-01T00:00:00Z',
  };
}

describe('Unit: useJoinRequestStore', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useJoinRequestStore.getState().reset();
  });

  it('joinByCode success appends request to myRequests', async () => {
    const mockRequest = makeMockRequest('req_1', 'cls_1', 'PENDING');
    vi.mocked(api.post).mockResolvedValueOnce({ data: mockRequest });

    const result = await useJoinRequestStore.getState().joinByCode('JOIN1234');

    expect(result.success).toBe(true);
    expect(api.post).toHaveBeenCalledWith('/api/v1/join-requests/join-by-code', { joinCode: 'JOIN1234' });
    expect(useJoinRequestStore.getState().myRequests).toContainEqual(mockRequest);
  });

  it('joinByCode failure returns error message', async () => {
    vi.mocked(api.post).mockRejectedValueOnce({
      response: { data: { detail: 'Invalid join code' } },
    });

    const result = await useJoinRequestStore.getState().joinByCode('INVALID');

    expect(result.success).toBe(false);
    expect(result.error).toBe('Invalid join code');
    expect(useJoinRequestStore.getState().error).toBe('Invalid join code');
  });

  it('fetchClassRequests retrieves pending requests for class', async () => {
    const mockRequests = [makeMockRequest('req_1', 'cls_1', 'PENDING')];
    vi.mocked(api.get).mockResolvedValueOnce({ data: mockRequests });

    await useJoinRequestStore.getState().fetchClassRequests('cls_1', 'PENDING');

    expect(api.get).toHaveBeenCalledWith('/api/v1/join-requests/class/cls_1', {
      params: { status: 'PENDING' },
    });
    expect(useJoinRequestStore.getState().classRequests).toEqual(mockRequests);
  });

  it('decideRequest removes decided request from pending list', async () => {
    useJoinRequestStore.setState({
      classRequests: [
        makeMockRequest('req_1', 'cls_1', 'PENDING'),
        makeMockRequest('req_2', 'cls_1', 'PENDING'),
      ],
      schoolRequests: [],
      myRequests: [],
      loading: false,
      error: '',
    });

    vi.mocked(api.patch).mockResolvedValueOnce({
      data: makeMockRequest('req_1', 'cls_1', 'APPROVED'),
    });

    const result = await useJoinRequestStore.getState().decideRequest('req_1', 'APPROVED', {
      autoRollNo: true,
    });

    expect(result.success).toBe(true);
    expect(useJoinRequestStore.getState().classRequests.map((r) => r.id)).toEqual(['req_2']);
  });
});
