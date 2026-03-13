import React from "react";
import cn from "classnames";
import styles from "./Button.module.scss";

export type ButtonSize = "xs" | "s" | "m" | "l" | "xl";
export type ButtonColor = "default" | "green" | "red" | "blue" | "yellow";
export type ButtonType = "primary" | "secondary" | "ghost";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  size?: ButtonSize;
  color?: ButtonColor;
  typeStyle?: ButtonType;
  icon?: React.ReactNode;
  children: React.ReactNode;
  disabled?: boolean;
  fullWidth?: boolean;
  onClick?: (e: React.MouseEvent<HTMLButtonElement, MouseEvent>) => void;
}

const Button: React.FC<ButtonProps> = ({
  size = "m",
  color = "default",
  typeStyle = "primary",
  icon,
  children,
  disabled = false,
  fullWidth = false,
  onClick,
  type = "button",
  className = "",
  ...props
}) => {
  return (
    <button
      type={type}
      className={cn(
        styles.button,
        styles[`button--${size}`],
        styles[`button--${typeStyle}`],
        styles[`button--${typeStyle}--${color}`],
        { [styles["button--disabled"]]: disabled },
        { [styles["button--full-width"]]: fullWidth },
        className
      )}
      disabled={disabled}
      onClick={disabled ? undefined : onClick}
      {...props}
    >
      {icon && <span className={styles["button__icon"]}>{icon}</span>}
      <div className={styles[`button__pad--${size}`]} />
      <span className={styles["button__text"]}>{children}</span>
      <div className={styles[`button__pad--${size}`]} />
    </button>
  );
};

export default Button;
