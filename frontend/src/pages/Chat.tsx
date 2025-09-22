import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ChatSidebar } from "@/components/chat/ChatSidebar";
import { ChatMessage } from "@/components/chat/ChatMessage";
import { ChatInput } from "@/components/chat/ChatInput";
import { Menu, LogOut } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useToast } from "@/hooks/use-toast";

interface Message {
  id: string;
  content: string;
  sender: "user" | "assistant";
  timestamp: string;
}

interface ChatThread {
  id: string;
  title: string;
  lastMessage: string;
  timestamp: string;
  isActive: boolean;
  messages: Message[];
}

export const Chat = () => {
  const [threads, setThreads] = useState<ChatThread[]>([]);
  const [activeThreadId, setActiveThreadId] = useState<string | null>(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [streamingMessageId, setStreamingMessageId] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();
  const { toast } = useToast();
  const token = localStorage.getItem("token");

  const activeThread = threads.find((t) => t.id === activeThreadId);
  const messages = activeThread?.messages || [];

  /** 🔹 Scroll to bottom when messages change */
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  /** 🔹 Load all user threads on mount */
  useEffect(() => {
    if (!token) {
      navigate("/");
      return;
    }
    (async () => {
      try {
        const res = await fetch("http://127.0.0.1:8000/chat/threads", {
          headers: { Authorization: `Bearer ${token}` },
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Failed to load threads");

        const mapped = data.threads.map((t: any) => ({
          id: t.id,
          title: t.title || "Untitled Conversation",
          lastMessage: t.last_message || "",
          timestamp: new Date(t.created_at).toLocaleString(),
          isActive: false,
          messages: [],
        }));

        setThreads(mapped);
        if (mapped.length > 0) {
          selectThread(mapped[0].id);
        }
      } catch (err: any) {
        console.error("Error loading threads:", err);
        const errorMessage = err?.message || err?.detail || err?.toString() || "Failed to load conversations";
        toast({
          title: "Error",
          description: errorMessage,
          variant: "destructive",
        });
      }
    })();
  }, []);

  /** 🔹 Fetch messages for a thread */
  const selectThread = async (threadId: string) => {
    if (!token) return;
    try {
      const res = await fetch(
        `http://127.0.0.1:8000/chat/threads/${threadId}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to load messages");

      const mappedMsgs: Message[] = data.messages.map((m: any) => ({
        id: m.id,
        content: m.content,
        sender: m.role === "user" ? "user" : "assistant",
        timestamp: new Date(m.timestamp).toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        }),
      }));

      setThreads((prev) =>
        prev.map((t) =>
          t.id === threadId
            ? { ...t, messages: mappedMsgs, isActive: true }
            : { ...t, isActive: false }
        )
      );
      setActiveThreadId(threadId);
      setIsSidebarOpen(false);
    } catch (err: any) {
      console.error("Error in selectThread:", err);
      const errorMessage = err?.message || err?.detail || err?.toString() || "Failed to load messages";
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });
    }
  };

  /** 🔹 Create a temporary local thread until the first message hits backend */
  const createNewChat = () => {
    const tempId = `temp-${Date.now()}`;
    const newThread: ChatThread = {
      id: tempId,
      title: "New Conversation",
      lastMessage: "",
      timestamp: "now",
      isActive: true,
      messages: [],
    };
    setThreads((prev) => [
      newThread,
      ...prev.map((t) => ({ ...t, isActive: false })),
    ]);
    setActiveThreadId(tempId);
    setIsSidebarOpen(false);
  };

  /** 🔹 Refresh threads list from backend */
  const refreshThreads = async (preserveActiveThread: boolean = true) => {
    if (!token) return;
    try {
      const res = await fetch("http://127.0.0.1:8000/chat/threads", {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to load threads");

      const mapped = data.threads.map((t: any) => ({
        id: t.id,
        title: t.title || "Untitled Conversation",
        lastMessage: t.last_message || "",
        timestamp: new Date(t.created_at).toLocaleString(),
        isActive: preserveActiveThread ? t.id === activeThreadId : false,
        messages: [],
      }));

      setThreads(mapped);
    } catch (err: any) {
      console.error("Failed to refresh threads:", err);
    }
  };

  /** 🔹 Send a message (backend will auto-create a thread if needed) */
  const sendMessage = async (content: string) => {
    if (!token || !activeThreadId) return;

    const userMessage: Message = {
      id: `msg-${Date.now()}`,
      content,
      sender: "user",
      timestamp: new Date().toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      }),
    };

    // Optimistic UI update
    setThreads((prev) =>
      prev.map((t) =>
        t.id === activeThreadId
          ? {
              ...t,
              messages: [...t.messages, userMessage],
              lastMessage: content,
              timestamp: "now",
            }
          : t
      )
    );

    setIsLoading(true);
    
    // Create a placeholder assistant message for streaming
    const assistantMessageId = `msg-${Date.now() + 1}`;
    setStreamingMessageId(assistantMessageId);
    const assistantMessage: Message = {
      id: assistantMessageId,
      content: "",
      sender: "assistant",
      timestamp: new Date().toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      }),
    };

    // Add empty assistant message to show streaming indicator
    setThreads((prev) =>
      prev.map((t) =>
        t.id === activeThreadId
          ? {
              ...t,
              messages: [...t.messages, assistantMessage],
            }
          : t
      )
    );

    try {
      const requestBody = { 
        user_input: content,
        thread_id: activeThreadId.startsWith("temp-") ? null : activeThreadId,
        stream: true
      };
      console.log("Sending streaming request body:", requestBody);
      
      const res = await fetch("http://127.0.0.1:8000/chat/stream", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(requestBody),
      });

      if (!res.ok) {
        const errorData = await res.json();
        console.error("API Error Response:", errorData);
        const errorMessage = errorData.detail || errorData.message || `HTTP ${res.status}: Failed to send message`;
        throw new Error(errorMessage);
      }

      const reader = res.body?.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let finalThreadId = activeThreadId;
      let fullResponse = "";

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || "";

          for (const line of lines) {
            console.log("Received line:", line);
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6));
                console.log("Parsed data:", data);
                
                if (data.type === 'start') {
                  // Handle thread ID update
                  if (activeThreadId.startsWith("temp-")) {
                    finalThreadId = data.thread_id;
                    setActiveThreadId(finalThreadId);
                    setThreads((prev) =>
                      prev.map((t) =>
                        t.id === activeThreadId
                          ? {
                              ...t,
                              id: finalThreadId,
                              title: content.slice(0, 50) + (content.length > 50 ? "..." : ""),
                            }
                          : t
                      )
                    );
                    // Refresh threads list to show the new thread in sidebar with updated title
                    await refreshThreads();
                  }
                } else if (data.type === 'delta') {
                  // Update the streaming message
                  console.log("Received delta:", data.content);
                  fullResponse += data.content;
                  setThreads((prev) =>
                    prev.map((t) =>
                      t.id === finalThreadId
                        ? {
                            ...t,
                            messages: t.messages.map((msg) =>
                              msg.id === assistantMessageId
                                ? { ...msg, content: fullResponse }
                                : msg
                            ),
                            lastMessage: fullResponse,
                            timestamp: "now",
                          }
                        : t
                    )
                  );
                } else if (data.type === 'done') {
                  // Final update with complete response
                  fullResponse = data.full_response;
                  setStreamingMessageId(null); // Stop streaming indicator
                  setThreads((prev) =>
                    prev.map((t) =>
                      t.id === finalThreadId
                        ? {
                            ...t,
                            messages: t.messages.map((msg) =>
                              msg.id === assistantMessageId
                                ? { ...msg, content: fullResponse }
                                : msg
                            ),
                            lastMessage: fullResponse,
                            timestamp: "now",
                          }
                        : t
                    )
                  );
                } else if (data.type === 'error') {
                  setStreamingMessageId(null); // Stop streaming indicator
                  throw new Error(data.error);
                }
              } catch (parseError) {
                console.error("Error parsing streaming data:", parseError);
              }
            }
          }
        }
      }
    } catch (err: any) {
      console.error("Error in sendMessage:", err);
      const errorMessage = err?.message || err?.detail || err?.toString() || "An unknown error occurred";
      
      // Remove the streaming message on error
      setStreamingMessageId(null);
      setThreads((prev) =>
        prev.map((t) =>
          t.id === activeThreadId
            ? {
                ...t,
                messages: t.messages.filter((msg) => msg.id !== assistantMessageId),
              }
            : t
        )
      );
      
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    navigate("/");
    toast({
      title: "Logged out",
      description: "You have been successfully logged out.",
    });
  };

  return (
    <div className="h-screen flex bg-background">
      {/* Sidebar */}
      <ChatSidebar
        threads={threads}
        onSelectThread={selectThread}
        onNewChat={createNewChat}
        onDeleteThread={() => {}}
        onRenameThread={() => {}}
        isMobileOpen={isSidebarOpen}
        onMobileToggle={() => setIsSidebarOpen(!isSidebarOpen)}
      />

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="border-b bg-card/50 backdrop-blur-sm p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setIsSidebarOpen(true)}
              className="lg:hidden"
            >
              <Menu size={20} />
            </Button>
            <Button 
              variant="outline" 
              onClick={() => navigate("/dashboard")}
              className="ml-2"
            >
              Dashboard
            </Button>
            <div>
              <h1 className="font-semibold">
                {activeThread?.title || "New Conversation"}
              </h1>
              <p className="text-sm text-muted-foreground">AI Assistant</p>
            </div>
          </div>

          <Button
            variant="ghost"
            size="icon"
            onClick={handleLogout}
            className="text-muted-foreground hover:text-foreground"
          >
            <LogOut size={20} />
          </Button>
        </div>

        {/* Messages */}
        <ScrollArea className="flex-1">
          <div className="flex flex-col">
            {messages.length === 0 ? (
              <div className="flex-1 flex items-center justify-center p-8">
                <div className="text-center max-w-md">
                  <div className="w-16 h-16 bg-gradient-primary rounded-full flex items-center justify-center mx-auto mb-4">
                    <span className="text-white text-2xl">🤖</span>
                  </div>
                  <h2 className="text-xl font-semibold mb-2">
                    Start a conversation
                  </h2>
                  <p className="text-muted-foreground">
                    I'm here to help! Ask me anything or start with a simple
                    "Hello"
                  </p>
                </div>
              </div>
            ) : (
              messages.map((message) => (
                <ChatMessage 
                  key={message.id} 
                  message={message} 
                  isStreaming={message.id === streamingMessageId}
                />
              ))
            )}
            <div ref={messagesEndRef} />
          </div>
        </ScrollArea>

        {/* Input */}
        <ChatInput onSendMessage={sendMessage} isLoading={isLoading} />
      </div>
    </div>
  );
};
