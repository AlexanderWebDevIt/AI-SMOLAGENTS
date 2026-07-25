import './Button.css'

const Button = ({
  children,
  onClick,
  className = '',
  disabled = false,
  type = 'button',
  variant = 'default',
  size = 'md'
}) => {
  return (
    <button
      type={type}
      className={`btn btn-${variant} btn-${size} ${className}`}
      onClick={onClick}
      disabled={disabled}
    >
      {children}
    </button>
  )
}

export default Button
