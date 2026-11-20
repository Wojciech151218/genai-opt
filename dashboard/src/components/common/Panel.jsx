/**
 * Shared glass/surface column wrapper used across Live Monitor and Database Explorer grids.
 * @param {{
 *   className: string,
 *   title: string,
 *   headerRow?: boolean,
 *   headerActions?: import('react').ReactNode,
 *   children: import('react').ReactNode
 * }} props
 */
function Panel({ className, title, headerRow = false, headerActions = null, children }) {
  const showHeaderRow = headerRow || Boolean(headerActions);

  return (
    <div className={`${className} glass-panel`}>
      {showHeaderRow ? (
        <div className="pop-panel-header">
          <h2 className="panel-title" style={{ marginBottom: 0 }}>
            {title}
          </h2>
          {headerActions}
        </div>
      ) : (
        <h2 className="panel-title">{title}</h2>
      )}
      {children}
    </div>
  );
}

export default Panel;
