import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function calculateNewOrder(prevOrder: number | null, nextOrder: number | null): number {
  if (prevOrder === null && nextOrder === null) {
    return 1.0;
  }
  if (prevOrder === null && nextOrder !== null) {
    return nextOrder / 2;
  }
  if (prevOrder !== null && nextOrder === null) {
    return prevOrder + 1;
  }
  // Both are not null
  return (prevOrder! + nextOrder!) / 2;
}
