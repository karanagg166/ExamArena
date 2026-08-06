import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useSchoolClassStore } from '@/stores/useSchoolClassStore';
import { api } from '@/lib/axios';

vi.mock('@/lib/axios', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
  },
}));

describe('useSchoolClassStore', () => {
  beforeEach(() => {
    useSchoolClassStore.getState().reset();
    vi.clearAllMocks();
  });

  it('starts with initial state', () => {
    const state = useSchoolClassStore.getState();
    expect(state.classes).toEqual([]);
    expect(state.loading).toBe(false);
    expect(state.error).toBe('');
  });

  it('fetchClassesBySchool populates classes', async () => {
    const mockClasses = [{ id: 'c1', name: 'Grade 10A' }, { id: 'c2', name: 'Grade 10B' }];
    (api.get as any).mockResolvedValueOnce({ data: mockClasses });

    await useSchoolClassStore.getState().fetchClassesBySchool('school-1');

    expect(useSchoolClassStore.getState().classes).toEqual(mockClasses);
  });

  it('createClass returns success when API call succeeds', async () => {
    const newClass = { id: 'c3', name: 'Grade 11A', year: 2026, section: 'A' };
    (api.post as any).mockResolvedValueOnce({ data: newClass });

    const result = await useSchoolClassStore.getState().createClass({
      name: 'Grade 11A',
      year: 2026,
      section: 'A',
    });

    expect(result.success).toBe(true);
    expect(useSchoolClassStore.getState().classes).toContainEqual(newClass);
  });

  it('createClass handles duplicate class error message correctly', async () => {
    (api.post as any).mockRejectedValueOnce({
      isAxiosError: true,
      response: {
        status: 409,
        data: { detail: 'Class Grade 11A already exists.' },
      },
    });

    const result = await useSchoolClassStore.getState().createClass({
      name: 'Grade 11A',
      year: 2026,
      section: 'A',
    });

    expect(result.success).toBe(false);
    expect(result.error).toContain("Class 'Grade 11A' already exists of same name.");
  });

  it('deleteClass removes class by id', async () => {
    useSchoolClassStore.setState({
      classes: [{ id: 'c1', name: 'Class 1' }, { id: 'c2', name: 'Class 2' }],
    });

    (api.delete as any).mockResolvedValueOnce({});

    const success = await useSchoolClassStore.getState().deleteClass('c1');

    expect(success).toBe(true);
    expect(useSchoolClassStore.getState().classes).toEqual([{ id: 'c2', name: 'Class 2' }]);
  });
});
