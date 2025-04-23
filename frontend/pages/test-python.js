import { useState, useEffect } from 'react';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';

export default function TestPython() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const testPython = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/api/test-python');
      const data = await response.json();
      
      setResult(data);
    } catch (error) {
      console.error('Erro ao testar Python:', error);
      setError(error.message || 'Erro desconhecido');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-4">
      <h1 className="text-2xl font-bold mb-4">Teste de Execução do Python</h1>
      
      <Card className="w-full max-w-2xl mb-4">
        <CardContent className="p-4">
          <p className="mb-4">
            Esta página testa se o Python está funcionando corretamente no servidor.
            Clique no botão abaixo para executar o teste.
          </p>
          
          <Button 
            onClick={testPython} 
            disabled={loading}
            className="w-full"
          >
            {loading ? 'Testando...' : 'Testar Python'}
          </Button>
        </CardContent>
      </Card>
      
      {error && (
        <Card className="w-full max-w-2xl mb-4 bg-red-50">
          <CardContent className="p-4">
            <h2 className="text-xl font-bold text-red-600 mb-2">Erro</h2>
            <p className="text-red-600">{error}</p>
          </CardContent>
        </Card>
      )}
      
      {result && (
        <Card className="w-full max-w-2xl">
          <CardContent className="p-4">
            <h2 className="text-xl font-bold mb-2">Resultado</h2>
            
            {result.success ? (
              <div className="bg-green-50 p-4 rounded-md">
                <p className="text-green-600 font-bold">{result.message}</p>
                <pre className="mt-4 p-2 bg-gray-100 rounded overflow-auto text-sm">
                  {result.output}
                </pre>
              </div>
            ) : (
              <div className="bg-red-50 p-4 rounded-md">
                <p className="text-red-600 font-bold">{result.error}</p>
                {result.stderr && (
                  <div className="mt-4">
                    <h3 className="font-bold">Erro:</h3>
                    <pre className="p-2 bg-gray-100 rounded overflow-auto text-sm">
                      {result.stderr}
                    </pre>
                  </div>
                )}
                {result.stdout && (
                  <div className="mt-4">
                    <h3 className="font-bold">Saída:</h3>
                    <pre className="p-2 bg-gray-100 rounded overflow-auto text-sm">
                      {result.stdout}
                    </pre>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
