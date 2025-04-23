import { useState, useEffect } from "react";
import { Input } from "../components/ui/input";
import { Button } from "../components/ui/button";
import { Card, CardContent } from "../components/ui/card";
import { Send, MessageCircle, FileText, LayoutGrid, Smile, Settings, HelpCircle, LogOut, Calendar } from "lucide-react";
import { MessageFormatter } from "../components/MessageFormatter";

const chatDescriptions = {
  Acadêmico: "Consulte informações acadêmicas, notas, faltas, disciplinas e sobre a UNISAL.",
  Documentos: "Pesquise informações em documentos PDF como regulamentos e manuais.",
  Suporte: "Receba apoio emocional e orientações para lidar com ansiedade e estresse.",
  Tutoria: "Obtenha explicações detalhadas sobre conteúdos das disciplinas.",
  Planejamento: "Receba ajuda para organizar seus estudos e criar cronogramas eficientes."
};

export default function ChatAcademico() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [selectedChat, setSelectedChat] = useState("Acadêmico");
  const [studentRA, setStudentRA] = useState(""); // Inicializa vazio, será carregado do localStorage
  const [showRAModal, setShowRAModal] = useState(false);

  // Carregar o RA do localStorage ao iniciar o componente
  useEffect(() => {
    // Verificar se estamos no navegador (não no servidor)
    if (typeof window !== 'undefined') {
      const savedRA = localStorage.getItem('studentRA');
      if (savedRA) {
        setStudentRA(savedRA);
      }
    }
  }, []);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const newMessage = {
      role: "user",
      content: input,
      timestamp: new Date().toLocaleTimeString()
    };
    setMessages([...messages, newMessage]);
    setInput("");

    try {
      // Mostrar mensagem de carregamento com texto personalizado baseado no tipo de chat
      let loadingMessage = "Processando sua consulta...";

      switch(selectedChat) {
        case "Acadêmico":
          loadingMessage = "Consultando informações acadêmicas...";
          break;
        case "Documentos":
          loadingMessage = "Pesquisando nos documentos...";
          break;
        case "Suporte":
          loadingMessage = "Preparando suporte emocional...";
          break;
        case "Tutoria":
          loadingMessage = "Elaborando explicação...";
          break;
        case "Planejamento":
          loadingMessage = "Criando plano de estudos...";
          break;
      }

      setMessages([...messages, newMessage, { role: "bot", content: loadingMessage, loading: true }]);

      // Determinar o endpoint com base no tipo de chat selecionado
      let endpoint = "";
      let payload = {};

      switch(selectedChat) {
        case "Acadêmico":
          endpoint = "/api/academic";
          payload = { query: input, user_id: studentRA };
          break;
        case "Documentos":
          endpoint = "/api/rag";
          payload = { query: input };
          break;
        case "Suporte":
          endpoint = "/api/emotional";
          payload = { query: input };
          break;
        case "Tutoria":
          endpoint = "/api/tutor";
          payload = { query: input };
          break;
        case "Planejamento":
          endpoint = "/api/planning";
          payload = { query: input };
          break;
        default:
          endpoint = "/api/academic";
          payload = { query: input, user_id: studentRA };
      }

      const response = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error(`Erro na resposta: ${response.status}`);
      }

      const data = await response.json();

      // Obter a resposta da API
      let formattedResponse = data.response || data.resposta || "";

      // Garantir que a resposta seja uma string
      if (typeof formattedResponse !== 'string') {
        console.warn("Resposta não é uma string:", formattedResponse);
        formattedResponse = String(formattedResponse || "");
      }

      // Adicionar quebras de linha para melhorar a legibilidade
      if (formattedResponse.length > 100) {
        // Adicionar quebras de linha em pontos e vírgulas para textos longos
        formattedResponse = formattedResponse
          .replace(/\. /g, ".\n")
          .replace(/; /g, ";\n");
      }

      console.log("Resposta recebida:", formattedResponse);

      // Verificar a fonte da informação
      const source = data.source || "";

      // Atualizar mensagens removendo a mensagem de carregamento
      setMessages([...messages, newMessage, {
        role: "bot",
        content: formattedResponse,
        timestamp: new Date().toLocaleTimeString(),
        source: source
      }]);
    } catch (error) {
      console.error("Erro ao enviar mensagem:", error);
      setMessages([...messages, newMessage, {
        role: "bot",
        content: "Desculpe, ocorreu um erro ao processar sua consulta. Por favor, tente novamente mais tarde.",
        timestamp: new Date().toLocaleTimeString(),
        error: true
      }]);
    }
  };

  // Função para verificar se é necessário mostrar o modal de RA foi movida para sendMessageWithRACheck

  // Função para lidar com o envio do RA
  const handleRASubmit = (e) => {
    e.preventDefault();
    const raInput = document.getElementById("ra-input").value;
    if (raInput) {
      // Salvar no estado
      setStudentRA(raInput);

      // Salvar no localStorage para persistência
      if (typeof window !== 'undefined') {
        localStorage.setItem('studentRA', raInput);
      }

      // Fechar o modal
      setShowRAModal(false);

      console.log(`RA salvo: ${raInput}`);
    }
  };

  // Função para enviar mensagem com verificação de RA
  const sendMessageWithRACheck = async () => {
    if (selectedChat === "Acadêmico" && !studentRA) {
      setShowRAModal(true);
      return;
    }
    sendMessage();
  };

  return (
    <div className="flex h-screen relative">
      {/* Menu Lateral Flutuante */}
      <div className="absolute left-0 top-0 h-full w-16 bg-gray-900 text-white flex flex-col items-center p-4 space-y-4 shadow-lg rounded-r-xl">
        <div className="w-10 h-10 rounded-full border-2 border-white bg-blue-500 flex items-center justify-center text-white font-bold">U</div>
        <LayoutGrid className="w-8 h-8" />
        <Smile className="w-8 h-8" />
        <MessageCircle className="w-8 h-8" />
        <Settings className="w-8 h-8" />
        <HelpCircle className="w-8 h-8" />
        <LogOut className="w-8 h-8" />
      </div>

      <div className="flex flex-col items-center flex-grow bg-gray-100 p-5 ml-16">
        <h1 className="text-2xl font-bold mb-5">Portal Acadêmico AI</h1>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-5">
          {Object.keys(chatDescriptions).map((chat) => (
            <Button
              key={chat}
              variant="outline"
              className="w-40 h-40 flex flex-col items-center justify-center"
              onClick={() => setSelectedChat(chat)}
            >
              {chat === "Acadêmico" ? <LayoutGrid className="w-12 h-12 mb-2" /> : null}
              {chat === "Documentos" ? <FileText className="w-12 h-12 mb-2" /> : null}
              {chat === "Suporte" ? <Smile className="w-12 h-12 mb-2" /> : null}
              {chat === "Tutoria" ? <MessageCircle className="w-12 h-12 mb-2" /> : null}
              {chat === "Planejamento" ? <Calendar className="w-12 h-12 mb-2" /> : null}
              {chat}
            </Button>
          ))}
        </div>

        <div className="flex flex-col items-center mb-5">
          {selectedChat === "Acadêmico" && <LayoutGrid className="w-16 h-16 text-gray-700" />}
          {selectedChat === "Documentos" && <FileText className="w-16 h-16 text-gray-700" />}
          {selectedChat === "Suporte" && <Smile className="w-16 h-16 text-gray-700" />}
          {selectedChat === "Tutoria" && <MessageCircle className="w-16 h-16 text-gray-700" />}
          {selectedChat === "Planejamento" && <Calendar className="w-16 h-16 text-gray-700" />}
          <p className="text-lg font-semibold mt-2">{selectedChat}</p>
          <p className="text-sm text-gray-500 text-center max-w-md">{chatDescriptions[selectedChat]}</p>

          {/* Mostrar RA e botão para alterar quando estiver no chat Acadêmico */}
          {selectedChat === "Acadêmico" && studentRA && (
            <div className="mt-2 flex items-center">
              <span className="text-sm text-blue-600 font-medium">RA: {studentRA}</span>
              <button
                className="ml-2 text-xs text-gray-500 underline"
                onClick={() => setShowRAModal(true)}
              >
                Alterar
              </button>
              <button
                className="ml-2 text-xs text-red-500 underline"
                onClick={() => {
                  setStudentRA("");
                  localStorage.removeItem("studentRA");
                }}
              >
                Limpar
              </button>
            </div>
          )}
        </div>

        <Card className="w-full max-w-2xl h-96 overflow-y-auto p-4 bg-white rounded-xl shadow-md">
          <CardContent>
            {messages.map((msg, index) => (
              <div key={index} className={`mb-3 p-3 rounded-lg ${msg.role === "user" ? "bg-blue-100 text-right" : "bg-gray-200 text-left"} ${msg.loading ? "animate-pulse" : ""}`}>
                {msg.role === "user" ? (
                  <div>
                    <div className="font-medium">
                      <MessageFormatter content={msg.content} />
                    </div>
                    {msg.timestamp && (
                      <div className="text-xs mt-1 text-gray-600">
                        {msg.timestamp}
                      </div>
                    )}
                  </div>
                ) : (
                  <div>
                    {msg.loading ? (
                      <div className="flex items-center">
                        <div className="mr-2">Processando</div>
                        <div className="flex space-x-1">
                          <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: "0ms" }}></div>
                          <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: "150ms" }}></div>
                          <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: "300ms" }}></div>
                        </div>
                      </div>
                    ) : (
                      <div>
                        <MessageFormatter content={msg.content} className="whitespace-pre-line" />
                        <div className="flex justify-between items-center">
                          {msg.timestamp && (
                            <div className={`text-xs mt-1 ${msg.error ? "text-red-500" : "text-gray-500"}`}>
                              {msg.timestamp}
                            </div>
                          )}
                          {msg.source === "web" && (
                            <div className="text-xs mt-1 text-blue-500 flex items-center">
                              <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9" />
                              </svg>
                              Fonte: Web
                            </div>
                          )}
                          {msg.source === "database" && (
                            <div className="text-xs mt-1 text-green-500 flex items-center">
                              <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2 1.5 3 3.5 3s3.5-1 3.5-3V7c0-2-1.5-3-3.5-3S4 5 4 7zm14-3.5C16.5 2 15 3 15 5v14c0 2 1.5 3 3.5 3s3.5-1 3.5-3V5c0-2-1.5-3-3.5-3z" />
                              </svg>
                              Fonte: Banco de Dados
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </CardContent>
        </Card>

        <div className="flex w-full max-w-2xl mt-4">
          <div className="flex items-center justify-center bg-gray-300 p-2 rounded-l-lg">
            <span className="font-bold text-gray-700">AI</span>
          </div>
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Digite sua pergunta..."
            className="flex-1 border-none"
          />
          <Button onClick={sendMessageWithRACheck} className="flex items-center"><Send className="mr-2"/> Enviar</Button>
        </div>
      </div>

      {/* Modal para solicitar RA */}
      {showRAModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg shadow-lg w-96">
            <h2 className="text-xl font-bold mb-4">Informe seu RA</h2>
            <p className="mb-4">Para consultar informações acadêmicas como notas e faltas, é necessário informar seu RA (Registro Acadêmico).</p>
            <p className="mb-4 text-sm text-gray-600">Exemplo: 201268, 123456, etc.</p>
            <form onSubmit={handleRASubmit}>
              <input
                id="ra-input"
                type="text"
                placeholder="Digite seu RA"
                className="w-full p-2 border border-gray-300 rounded mb-4"
                defaultValue={studentRA}
              />
              <div className="flex justify-end">
                <button
                  type="button"
                  className="px-4 py-2 bg-gray-300 rounded mr-2"
                  onClick={() => setShowRAModal(false)}
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-500 text-white rounded"
                >
                  Confirmar
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
