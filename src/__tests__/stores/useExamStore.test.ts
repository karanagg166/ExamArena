/* eslint-disable @typescript-eslint/no-explicit-any */
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useExamStore } from '@/stores/useExamStore';
import { api } from '@/lib/axios';

vi.mock('@/lib/axios', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
  },
}));

describe('useExamStore', () => {
  beforeEach(() => {
    useExamStore.getState().reset();
    vi.clearAllMocks();
  });

  it('starts with initial empty state', () => {
    const state = useExamStore.getState();
    expect(state.exams).toEqual([]);
    expect(state.currentExam).toBeNull();
    expect(state.loading).toBe(false);
    expect(state.error).toBeNull();
  });

  it('fetchExams fetches list of exams successfully', async () => {
    const mockExams = [
      { id: '1', name: 'Math Exam', type: 'MIDTERM' },
      { id: '2', name: 'Science Quiz', type: 'QUIZ' },
    ];
    (api.get as any).mockResolvedValueOnce({ data: mockExams });

    await useExamStore.getState().fetchExams();

    const state = useExamStore.getState();
    expect(state.exams).toEqual(mockExams);
    expect(state.loading).toBe(false);
    expect(state.error).toBeNull();
  });

  it('fetchExams sets error message when API call fails', async () => {
    (api.get as any).mockRejectedValueOnce({
      isAxiosError: true,
      response: { data: { detail: 'Failed to connect to database' } },
    });

    await useExamStore.getState().fetchExams();

    const state = useExamStore.getState();
    expect(state.error).toBe('Failed to connect to database');
    expect(state.loading).toBe(false);
  });

  it('fetchExamById updates currentExam state', async () => {
    const mockExam = { id: 'exam-99', name: 'Physics Final', type: 'FINAL' };
    (api.get as any).mockResolvedValueOnce({ data: mockExam });

    await useExamStore.getState().fetchExamById('exam-99');

    expect(useExamStore.getState().currentExam).toEqual(mockExam);
  });

  it('createExam posts data and updates state', async () => {
    const newExam = { id: 'e-100', name: 'History Quiz', type: 'QUIZ' };
    (api.post as any).mockResolvedValueOnce({ data: newExam });

    const created = await useExamStore.getState().createExam({
      name: 'History Quiz',
      description: 'Ch 1-4',
      scheduledAt: '2026-08-07T00:00:00Z',
      duration: 30,
      maxMarks: 50,
      isPublished: true,
      type: 'QUIZ',
    });

    expect(created).toEqual(newExam);
    expect(useExamStore.getState().exams).toContainEqual(newExam);
  });

  it('reset clears store state', () => {
    useExamStore.getState().setError('Some error');
    useExamStore.getState().reset();
    expect(useExamStore.getState().error).toBeNull();
  });
});
