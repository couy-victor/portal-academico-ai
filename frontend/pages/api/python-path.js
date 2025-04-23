// API route para verificar o caminho do Python
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

export default async function handler(req, res) {
  try {
    console.log(`[${new Date().toISOString()}] Verificando caminho do Python`);
    
    // Verificar o caminho do Python
    const { stdout: pythonPath, stderr: pythonPathError } = await execAsync('where python');
    
    // Verificar a versão do Python
    const { stdout: pythonVersion, stderr: pythonVersionError } = await execAsync('python --version');
    
    // Verificar o PATH do sistema
    const { stdout: envPath, stderr: envPathError } = await execAsync('echo %PATH%');
    
    return res.status(200).json({
      success: true,
      pythonPath: pythonPath.trim(),
      pythonVersion: pythonVersion.trim(),
      envPath: envPath.trim(),
      errors: {
        pythonPathError: pythonPathError || null,
        pythonVersionError: pythonVersionError || null,
        envPathError: envPathError || null
      }
    });
  } catch (error) {
    console.error(`[${new Date().toISOString()}] Erro ao verificar caminho do Python:`, error);
    
    return res.status(500).json({
      error: 'Erro ao verificar caminho do Python',
      message: error.message,
      stack: error.stack
    });
  }
}
