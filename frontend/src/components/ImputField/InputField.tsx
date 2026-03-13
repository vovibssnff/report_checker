import React from "react";
import cn from "classnames";
import styles from "./InputField.module.scss";
import CrossIcon from "../icons/CrossIcon/CrossIcon";

type InputFieldProps = {
    label: string;
    type?: "text" | "number" | "date" | "email" | "password";
    value: string | number;
    onChange: (value: string) => void;
    placeholder?: string;
    required?: boolean;
    className?: string;

    min?: number | string;
    max?: number | string;
    step?: number;
    pattern?: string;
    maxLength?: number;
    minLength?: number;
    inputMode?:
        | "text"
        | "numeric"
        | "decimal"
        | "search"
        | "tel"
        | "email"
        | "url";

    disabled?: boolean;
    readOnly?: boolean;
};

const InputField: React.FC<InputFieldProps> = ({
    label,
    type = "text",
    value,
    onChange,
    placeholder = "",
    required = false,
    className,

    min,
    max,
    step,
    pattern,
    maxLength,
    minLength,
    inputMode,
    disabled,
    readOnly,
}) => {
    const showClear = String(value).length > 0 && !readOnly && !disabled;

    return (
        <div className={styles["input-field"]}>
            {label && (
                <label className={cn(styles["input-field__label"], "h50")}>
                    {label}
                </label>
            )}

            <div className={styles["input-field__wrapper"]}>
                {showClear && (
                    <button
                        type="button"
                        className={styles["input-field__clear"]}
                        onClick={() => onChange("")}
                    >
                        <CrossIcon size="0.875rem" color="#000000" />
                    </button>
                )}

                <input
                    type={type}
                    value={value}
                    onChange={(e) => onChange(e.target.value)}
                    placeholder={placeholder}
                    className={cn(styles["input-field__input"], className)}
                    required={required}
                    min={min}
                    max={max}
                    step={step}
                    pattern={pattern}
                    maxLength={maxLength}
                    minLength={minLength}
                    inputMode={inputMode}
                    disabled={disabled}
                    readOnly={readOnly}
                />
            </div>
        </div>
    );
};

export default InputField;
