// components/ProtectedRoute.tsx
import { useGate } from "@/lib/GateContext";
import { useLocation } from "wouter";

export default function ProtectedRoute({ children }: { children: JSX.Element }) {
  const { hasEntered } = useGate();
  const [location, setLocation] = useLocation();

  if (!hasEntered) {
    setLocation("/enter");
    return null;
  }

  return children;
}