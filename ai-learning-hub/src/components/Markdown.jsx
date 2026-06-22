import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'
import Diagram from './Diagram.jsx'

export default function Markdown({ children }) {
  return (
    <div className="md">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          code({ inline, className, children, ...props }) {
            const match = /language-(\w+)/.exec(className || '')
            if (match && match[1] === 'diagram') {
              return <Diagram spec={children} />
            }
            if (inline || !match) {
              return (
                <code className={className} {...props}>
                  {children}
                </code>
              )
            }
            return (
              <SyntaxHighlighter
                language={match[1]}
                style={oneDark}
                customStyle={{
                  margin: 0,
                  background: '#0d1019',
                  fontSize: '13px',
                  padding: '18px 20px',
                }}
                codeTagProps={{ style: { fontFamily: "'JetBrains Mono', ui-monospace, Menlo, Consolas, monospace" } }}
              >
                {String(children).replace(/\n$/, '')}
              </SyntaxHighlighter>
            )
          },
        }}
      >
        {children}
      </ReactMarkdown>
    </div>
  )
}
