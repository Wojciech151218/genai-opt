/**
 * Floating notification banner shown for transient warnings (e.g., offline engine commands).
 * @param {{ message: string | null }} props
 */
function Toast({ message }) {
  if (!message) {
    return null;
  }

  return <div className="toast">{message}</div>;
}

export default Toast;
