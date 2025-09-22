import { useState } from "react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { 
  MessageSquare, 
  Plus, 
  MoreHorizontal, 
  Trash2, 
  Edit3,
  Menu,
  X
} from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

interface ChatThread {
  id: string;
  title: string;
  lastMessage: string;
  timestamp: string;
  isActive: boolean;
}

interface ChatSidebarProps {
  threads: ChatThread[];
  onSelectThread: (threadId: string) => void;
  onNewChat: () => void;
  onDeleteThread: (threadId: string) => void;
  onRenameThread: (threadId: string, newTitle: string) => void;
  isMobileOpen: boolean;
  onMobileToggle: () => void;
}

export const ChatSidebar = ({
  threads,
  onSelectThread,
  onNewChat,
  onDeleteThread,
  onRenameThread,
  isMobileOpen,
  onMobileToggle
}: ChatSidebarProps) => {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState("");

  const handleRename = (thread: ChatThread) => {
    setEditingId(thread.id);
    setEditTitle(thread.title);
  };

  const handleSaveRename = (threadId: string) => {
    if (editTitle.trim()) {
      onRenameThread(threadId, editTitle.trim());
    }
    setEditingId(null);
    setEditTitle("");
  };

  const handleCancelRename = () => {
    setEditingId(null);
    setEditTitle("");
  };

  return (
    <>
      {/* Mobile Backdrop */}
      {isMobileOpen && (
        <div 
          className="fixed inset-0 bg-black/20 backdrop-blur-sm z-40 lg:hidden"
          onClick={onMobileToggle}
        />
      )}

      {/* Sidebar */}
      <div 
        className={`
          fixed lg:relative inset-y-0 left-0 z-50 w-80 bg-sidebar
          border-r transform transition-transform duration-200 ease-in-out
          ${isMobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        `}
      >
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b">
            <h2 className="font-semibold text-lg">Conversations</h2>
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="icon"
                onClick={onNewChat}
                className="hover:bg-sidebar-hover"
              >
                <Plus size={18} />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                onClick={onMobileToggle}
                className="lg:hidden hover:bg-sidebar-hover"
              >
                <X size={18} />
              </Button>
            </div>
          </div>

          {/* Chat Threads */}
          <ScrollArea className="flex-1">
            <div className="p-2 space-y-1">
              {threads.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <MessageSquare className="h-12 w-12 mx-auto mb-3 opacity-50" />
                  <p className="text-sm">No conversations yet</p>
                  <p className="text-xs">Start a new chat to get going!</p>
                </div>
              ) : (
                threads.map((thread) => (
                  <div
                    key={thread.id}
                    className={`
                      group relative p-3 rounded-lg cursor-pointer transition-colors
                      ${thread.isActive 
                        ? 'bg-primary/10 border border-primary/20' 
                        : 'hover:bg-sidebar-hover'
                      }
                    `}
                    onClick={() => onSelectThread(thread.id)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        {editingId === thread.id ? (
                          <input
                            type="text"
                            value={editTitle}
                            onChange={(e) => setEditTitle(e.target.value)}
                            onBlur={() => handleSaveRename(thread.id)}
                            onKeyDown={(e) => {
                              if (e.key === 'Enter') handleSaveRename(thread.id);
                              if (e.key === 'Escape') handleCancelRename();
                            }}
                            className="w-full bg-background border rounded px-2 py-1 text-sm"
                            autoFocus
                            onClick={(e) => e.stopPropagation()}
                          />
                        ) : (
                          <>
                            <h3 className="font-medium text-sm truncate mb-1">
                              {thread.title}
                            </h3>
                            <p className="text-xs text-muted-foreground truncate">
                              {thread.lastMessage}
                            </p>
                            <p className="text-xs text-muted-foreground mt-1">
                              {thread.timestamp}
                            </p>
                          </>
                        )}
                      </div>

                      {editingId !== thread.id && (
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-6 w-6 opacity-0 group-hover:opacity-100 hover:bg-sidebar-hover"
                              onClick={(e) => e.stopPropagation()}
                            >
                              <MoreHorizontal size={14} />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem
                              onClick={(e) => {
                                e.stopPropagation();
                                handleRename(thread);
                              }}
                            >
                              <Edit3 size={14} className="mr-2" />
                              Rename
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              onClick={(e) => {
                                e.stopPropagation();
                                onDeleteThread(thread.id);
                              }}
                              className="text-destructive focus:text-destructive"
                            >
                              <Trash2 size={14} className="mr-2" />
                              Delete
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </ScrollArea>
        </div>
      </div>
    </>
  );
};