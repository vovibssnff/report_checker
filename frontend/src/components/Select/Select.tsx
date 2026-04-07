import React, { useState, useRef, useEffect } from "react";
import { AnimatePresence, motion } from "framer-motion";
import cn from "classnames";
import styles from "./Select.module.scss";
import CheckIcon from "../icons/CheckIcon/CheckIcon";

interface Option<T extends string | number> {
    value: T;
    label: string;
}

interface SelectProps<T extends string | number> {
    options: Option<T>[];
    value: T | null;
    setValue: (value: T | null) => void;
    placeholder?: string;
    className?: string;
    dropdownMaxHeight?: number;
    compact?: boolean;
    title?: string;
    icon?: React.ReactNode;
    allowNull?: boolean;
}

function Select<T extends string | number>({
    options,
    value,
    setValue,
    placeholder = "Выберите...",
    className,
    dropdownMaxHeight = 220,
    compact = false,
    title,
    icon,
    allowNull = false,
}: SelectProps<T>) {

    const [open, setOpen] = useState(false);
    const [dropUp, setDropUp] = useState(false);
    const [dropdownStyles, setDropdownStyles] = useState<React.CSSProperties>({});
    const ref = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (!open || !ref.current) return;

        const rect = ref.current.getBoundingClientRect();
        const viewportHeight = window.innerHeight;
        const ddHeight = Math.min(dropdownMaxHeight, options.length * 44 + 32);
        const spaceBelow = viewportHeight - rect.bottom - 8;
        const spaceAbove = rect.top - 8;

        if (spaceBelow >= ddHeight || spaceBelow > spaceAbove) {
            setDropUp(false);
            setDropdownStyles({
                top: "calc(100% + 8px)",
                bottom: "auto",
                maxHeight: Math.min(ddHeight, spaceBelow) + "px",
            });
        } else {
            setDropUp(true);
            setDropdownStyles({
                top: "auto",
                bottom: "calc(100% + 8px)",
                maxHeight: Math.min(ddHeight, spaceAbove) + "px",
            });
        }
    }, [open, options.length, dropdownMaxHeight]);

    useEffect(() => {
        if (!open) return;
        function handler(e: MouseEvent) {
            if (!ref.current?.contains(e.target as Node)) setOpen(false);
        }
        document.addEventListener("mousedown", handler);
        return () => document.removeEventListener("mousedown", handler);
    }, [open]);

    const selected = options.find(opt => opt.value === value);

    return (
        <div className={cn(styles.select, className, compact && styles["select--compact"])} ref={ref}>
            {title && (
                <label className={styles["select__label"]}>{title}</label>
            )}
            <button
                className={cn(styles["select__btn"], compact && styles["select__btn--compact"])}
                type="button"
                onClick={() => setOpen(v => !v)}
            >
                {icon && <span className={styles["select__icon"]}>{icon}</span>}
                <span className={styles["select__btn-value"]}>
                    {selected?.label ?? placeholder}
                </span>
            </button>

            <AnimatePresence>
                {open && (
                    <motion.div
                        className={cn(styles["select__dropdown"], dropUp && styles["select__dropdown--up"])}
                        initial={{ opacity: 0, scale: 0.86 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.86 }}
                        transition={{ duration: 0.1, ease: "easeOut" }}
                        style={dropdownStyles}
                    >
                        {allowNull && (
                            <button
                                type="button"
                                className={cn(styles["select__option"], compact && styles["select__option--compact"])}
                                onClick={() => { setValue(null); setOpen(false); }}
                            >
                                <span>{placeholder}</span>
                            </button>
                        )}

                        {options.map(opt => (
                            <button
                                type="button"
                                key={String(opt.value)}
                                className={cn(styles["select__option"], {
                                    [styles["select__option--active"]]: value === opt.value,
                                }, compact && styles["select__option--compact"])}
                                onClick={() => { setValue(opt.value); setOpen(false); }}
                            >
                                <span>{opt.label}</span>
                                {value === opt.value && (
                                    <span className={styles["select__option-icon"]}>
                                        <CheckIcon size="1.25rem" color="#000000" />
                                    </span>
                                )}
                            </button>
                        ))}
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}

export default Select;
