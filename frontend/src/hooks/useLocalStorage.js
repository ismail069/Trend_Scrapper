import { useEffect, useState } from "react";
import { loadStoredValue, saveStoredValue } from "../utils/storage";

export function useLocalStorage(key, initialValue) {
  const [value, setValue] = useState(() => loadStoredValue(key, initialValue));

  useEffect(() => {
    saveStoredValue(key, value);
  }, [key, value]);

  return [value, setValue];
}

