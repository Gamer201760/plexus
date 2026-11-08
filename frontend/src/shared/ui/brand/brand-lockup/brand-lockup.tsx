import { BrandMark } from "../brand-mark/brand-mark"
import { WORDMARK_PATHS } from "../mark-paths"
import styles from "./brand-lockup.module.css"
export function BrandLockup() {
  return (
    <span className={styles.lockup} aria-hidden="true">
      <BrandMark kind="symbol" rings={1} size="sm" decorative />
      <svg viewBox="0 -56 228 73" aria-hidden="true">
        <path d={WORDMARK_PATHS.word} fillRule="evenodd" />
      </svg>
    </span>
  )
}
