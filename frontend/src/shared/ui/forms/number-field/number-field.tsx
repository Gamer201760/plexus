import { TextField, type TextFieldProps } from "../text-field/text-field"

export interface NumberFieldProps extends Omit<TextFieldProps, "type" | "inputMode"> {}

export function NumberField(props: NumberFieldProps) {
  return <TextField {...props} inputMode="numeric" />
}
