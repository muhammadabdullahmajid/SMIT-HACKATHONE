import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Bot, User } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import "highlight.js/styles/github.css";

interface ChatMessageProps {
  message: {
    id: string;
    content: string;
    sender: "user" | "assistant";
    timestamp: string;
  };
  isStreaming?: boolean;
}

export const ChatMessage = ({ message, isStreaming = false }: ChatMessageProps) => {
  const isUser = message.sender === "user";

  return (
    <div className={`flex gap-3 p-4 ${isUser ? "flex-row-reverse" : ""}`}>
      <Avatar className="h-8 w-8 shrink-0">
        <AvatarFallback className={isUser ? "bg-primary text-primary-foreground" : "bg-muted"}>
          {isUser ? <User size={16} /> : <Bot size={16} />}
        </AvatarFallback>
      </Avatar>
      
      <div className={`flex flex-col max-w-[80%] ${isUser ? "items-end" : "items-start"}`}>
        <div
          className={`
            rounded-lg px-4 py-3 text-sm prose prose-sm max-w-none
            ${isUser 
              ? "bg-primary text-primary-foreground" 
              : "bg-muted border"
            }
            ${isStreaming ? "animate-pulse" : ""}
          `}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap m-0">{message.content}</p>
          ) : (
            <div className="prose-headings:text-foreground prose-p:text-foreground prose-strong:text-foreground prose-code:text-foreground prose-pre:bg-muted prose-pre:border">
              <div className={isStreaming ? "streaming-text" : ""}>
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  rehypePlugins={[rehypeHighlight]}
                  components={{
                    p: ({ children }) => <p className="m-0 mb-2 last:mb-0">{children}</p>,
                    strong: ({ children }) => <strong className="font-bold text-foreground">{children}</strong>,
                    em: ({ children }) => <em className="italic text-foreground">{children}</em>,
                    code: ({ children, className }) => {
                      const isInline = !className;
                      return isInline ? (
                        <code className="bg-muted px-1 py-0.5 rounded text-sm font-mono">{children}</code>
                      ) : (
                        <code className={className}>{children}</code>
                      );
                    },
                    pre: ({ children }) => (
                      <pre className="bg-muted p-3 rounded-lg overflow-x-auto border">
                        {children}
                      </pre>
                    ),
                    ul: ({ children }) => <ul className="list-disc list-inside my-2">{children}</ul>,
                    ol: ({ children }) => <ol className="list-decimal list-inside my-2">{children}</ol>,
                    li: ({ children }) => <li className="my-1">{children}</li>,
                    blockquote: ({ children }) => (
                      <blockquote className="border-l-4 border-muted-foreground pl-4 italic my-2">
                        {children}
                      </blockquote>
                    ),
                    h1: ({ children }) => <h1 className="text-xl font-bold my-2">{children}</h1>,
                    h2: ({ children }) => <h2 className="text-lg font-bold my-2">{children}</h2>,
                    h3: ({ children }) => <h3 className="text-base font-bold my-2">{children}</h3>,
                  }}
                >
                  {message.content}
                </ReactMarkdown>
              </div>
            </div>
          )}
        </div>
        <span className="text-xs text-muted-foreground mt-1">
          {message.timestamp}
        </span>
      </div>
    </div>
  );
};