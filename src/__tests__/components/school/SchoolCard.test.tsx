import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import SchoolCard from '@/components/school/SchoolCard';
import type { School, SchoolType } from '@/types/school';

const mockPush = vi.fn();
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
}));

const mockSchool: School = {
  id: 'sch_1',
  name: 'Delhi Public International School',
  address: '123 Ring Road, South Extension',
  schoolCode: 'SCH-DEL-01',
  type: 'PUBLIC' as SchoolType,
  city: 'New Delhi',
  state: 'Delhi',
  country: 'India',
  pincode: '110001',
  phoneNo: '+919876543210',
  email: 'admin@dpis.edu.in',
  principalName: 'Dr. Sharma',
  createdBy: 'usr_p1',
  createdAt: '2024-01-01T00:00:00Z',
  updatedAt: '2024-01-01T00:00:00Z',
};

describe('Component: SchoolCard (C12-C16)', () => {
  it('C12: renders school name, code, type, and location', () => {
    render(<SchoolCard school={mockSchool} />);

    expect(screen.getByText('Delhi Public International School')).toBeInTheDocument();
    expect(screen.getByText('SCH-DEL-01')).toBeInTheDocument();
    expect(screen.getByText('Public')).toBeInTheDocument();
    expect(screen.getByText('New Delhi')).toBeInTheDocument();
    expect(screen.getByText('Delhi')).toBeInTheDocument();
    expect(screen.getByText('Dr. Sharma')).toBeInTheDocument();
    expect(screen.getByText('admin@dpis.edu.in')).toBeInTheDocument();
  });

  it('navigates to school detail on card click', () => {
    const handleClick = vi.fn();
    render(<SchoolCard school={mockSchool} onClick={handleClick} />);

    fireEvent.click(screen.getByText('Delhi Public International School'));

    expect(handleClick).toHaveBeenCalledWith(mockSchool);
    expect(mockPush).toHaveBeenCalledWith('/schools/sch_1');
  });
});
