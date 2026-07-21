import {
  useEffect,
  useSyncExternalStore,
} from "react";
import {
  RouterProvider,
} from "react-router";

import {
  applyLanguage,
  getLanguage,
  getServerLanguage,
  subscribeLanguage,
} from "./i18n/language";
import { router } from "./routes/router";

export function App() {
  const language = useSyncExternalStore(
    subscribeLanguage,
    getLanguage,
    getServerLanguage,
  );

  useEffect(() => {
    applyLanguage(language);
  }, [language]);

  return (
    <RouterProvider
      key={language}
      router={router}
    />
  );
}

export default App;
