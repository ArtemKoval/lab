// The pack's words for the signed-in pages: one fetch of the pack endpoint,
// provided to every component that labels a domain word or renders an award.

import { type ReactNode } from "react";
import { api } from "./api";
import { useLoad } from "./useLoad";
import { PackWordsContext } from "./vocabulary";

export function PackWords({ children }: Readonly<{ children: ReactNode }>) {
  const { data } = useLoad(api.getPack);
  return (
    <PackWordsContext.Provider value={{ vocabulary: data?.vocabulary ?? null }}>
      {children}
    </PackWordsContext.Provider>
  );
}
