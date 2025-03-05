import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Send, MessageCircle, Image, FileText, Menu, LayoutGrid, Smile, Settings, HelpCircle, LogOut } from "lucide-react";

const chatDescriptions = {
  ChatGPT: "Um assistente de IA para perguntas gerais.",
  ChatTEC: "Assistente acadêmico para suporte estudantil.",
  GerarImagem: "Gere imagens a partir de descrições.",
  ResumirTexto: "Resuma textos longos automaticamente."
};

export default function ChatAcademico() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [selectedChat, setSelectedChat] = useState("ChatGPT");

  const sendMessage = async () => {
    if (!input.trim()) return;
    
    const newMessage = { role: "user", content: input };
    setMessages([...messages, newMessage]);
    setInput("");
    
    const response = await fetch("http://localhost:8000/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pergunta: input, aluno_id: 1, chat: selectedChat }),
    });
    
    const data = await response.json();
    setMessages([...messages, newMessage, { role: "bot", content: data.resposta }]);
  };

  return (
    <div className="flex h-screen relative">
      {/* Menu Lateral Flutuante */}
      <div className="absolute left-0 top-0 h-full w-16 bg-gray-900 text-white flex flex-col items-center p-4 space-y-4 shadow-lg rounded-r-xl">
        <img src="/profile-pic.png" alt="Perfil" className="w-10 h-10 rounded-full border-2 border-white" />
        <LayoutGrid className="w-8 h-8" />
        <Smile className="w-8 h-8" />
        <MessageCircle className="w-8 h-8" />
        <Settings className="w-8 h-8" />
        <HelpCircle className="w-8 h-8" />
        <LogOut className="w-8 h-8" />
      </div>

      <div className="flex flex-col items-center flex-grow bg-gray-100 p-5 ml-16">
        <h1 className="text-2xl font-bold mb-5">TECgpt-Acadêmico</h1>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-5">
          {Object.keys(chatDescriptions).map((chat) => (
            <Button 
              key={chat}
              variant="outline" 
              className="w-40 h-40 flex flex-col items-center justify-center" 
              onClick={() => setSelectedChat(chat)}
            >
              {chat === "ChatGPT" || chat === "ChatTEC" ? <MessageCircle className="w-12 h-12 mb-2" /> : null}
              {chat === "GerarImagem" ? <Image className="w-12 h-12 mb-2" /> : null}
              {chat === "ResumirTexto" ? <FileText className="w-12 h-12 mb-2" /> : null}
              {chat}
            </Button>
          ))}
        </div>

        <div className="flex flex-col items-center mb-5">
          <MessageCircle className="w-16 h-16 text-gray-700" />
          <p className="text-lg font-semibold mt-2">{selectedChat}</p>
          <p className="text-sm text-gray-500 text-center max-w-md">{chatDescriptions[selectedChat]}</p>
        </div>
        
        <Card className="w-full max-w-2xl h-96 overflow-y-auto p-4 bg-white rounded-xl shadow-md">
          <CardContent>
            {messages.map((msg, index) => (
              <div key={index} className={`mb-3 p-2 rounded-lg ${msg.role === "user" ? "bg-blue-100 text-right" : "bg-gray-200 text-left"}`}>
                {msg.content}
              </div>
            ))}
          </CardContent>
        </Card>

        <div className="flex w-full max-w-2xl mt-4">
          <div className="flex items-center justify-center bg-gray-300 p-2 rounded-l-lg">
            <img src="/unisal-icon.png" alt="Unisal" className="w-6 h-6" />
          </div>
          <Input 
            value={input} 
            onChange={(e) => setInput(e.target.value)} 
            placeholder="Digite sua pergunta..."
            className="flex-1 border-none"
          />
          <Button onClick={sendMessage} className="flex items-center"><Send className="mr-2"/> Enviar</Button>
        </div>
      </div>
    </div>
  );
}
