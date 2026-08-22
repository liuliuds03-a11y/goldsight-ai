/** 通用占位页面组件 */
export default function PlaceholderPage({ title, description }: { title: string; description: string }) {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '60vh',
      gap: '16px',
      textAlign: 'center',
    }}>
      <h1 style={{
        fontSize: '32px',
        fontWeight: 700,
        background: 'linear-gradient(90deg, var(--color-primary), #f0c040)',
        WebkitBackgroundClip: 'text',
        WebkitTextFillColor: 'transparent',
      }}>
        {title}
      </h1>
      <p style={{ color: 'var(--color-text-secondary)', fontSize: '15px', maxWidth: '480px' }}>
        {description}
      </p>
      <span style={{
        display: 'inline-block',
        marginTop: '8px',
        padding: '4px 12px',
        fontSize: '12px',
        color: 'var(--color-primary)',
        background: 'rgba(212, 160, 23, 0.1)',
        border: '1px solid rgba(212, 160, 23, 0.2)',
        borderRadius: '4px',
      }}>
        模块开发中，即将上线
      </span>
    </div>
  )
}
