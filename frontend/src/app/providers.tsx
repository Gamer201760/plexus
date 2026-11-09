import { QueryClientProvider } from "@tanstack/react-query"
import { type ReactNode, useState } from "react"
import { createQueryClient } from "@/shared/api"
import { LocaleProvider } from "@/shared/i18n"
import { LayerHost, ToastHost } from "@/shared/ui"

export interface ProvidersProps {
  readonly children: ReactNode
}

export function Providers({ children }: ProvidersProps) {
  const [client] = useState(createQueryClient)
  return (
    <QueryClientProvider client={client}>
      <LocaleProvider>
        <LayerHost>
          <ToastHost>{children}</ToastHost>
        </LayerHost>
      </LocaleProvider>
    </QueryClientProvider>
  )
}
