import './Message.css'

const Message = ({ role, content, steps }) => {
  return (
    <div className={`message ${role}`}>
      <div className="message-avatar">
        {role === 'user' ? '👤' : '🤖'}
      </div>
      <div className="message-content">
        <div className="message-text">{content}</div>
        {steps && steps.length > 0 && (
          <div className="tool-steps">
            <details>
              <summary>Инструментов: {steps.length}</summary>
              {steps.map((step, i) => (
                <div key={i} className="step">
                  <code>{step.tool}</code>
                  <span className="step-args">{JSON.stringify(step.args)}</span>
                </div>
              ))}
            </details>
          </div>
        )}
      </div>
    </div>
  )
}

export default Message
