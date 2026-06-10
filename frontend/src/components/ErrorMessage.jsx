import { CircleAlert } from "lucide-react";

export function ErrorMessage({ message }) {
  if (!message) return null;
  return (
    <div className="error-message" role="alert">
      <CircleAlert size={18} />
      <span>{message}</span>
    </div>
  );
}

