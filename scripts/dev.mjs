import { spawn } from 'node:child_process'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

const root = dirname(dirname(fileURLToPath(import.meta.url)))
const frontend = join(root, 'frontend')
const vite = join(frontend, 'node_modules', 'vite', 'bin', 'vite.js')

const children = []

function run(name, command, args, cwd) {
  const child = spawn(command, args, {
    cwd,
    stdio: 'inherit',
    env: { ...process.env, PYTHONUTF8: '1' },
  })
  children.push(child)
  child.on('exit', (code) => {
    if (shuttingDown) return
    console.log(`[${name}] exited with code ${code}`)
    shutdown(code ?? 0)
  })
  return child
}

let shuttingDown = false
function shutdown(code = 0) {
  shuttingDown = true
  for (const child of children) {
    if (!child.killed) child.kill()
  }
  setTimeout(() => process.exit(code), 200)
}

process.on('SIGINT', () => shutdown(0))
process.on('SIGTERM', () => shutdown(0))

run('api', 'python', ['-m', 'uvicorn', 'augar_engine.api.app:app', '--host', '127.0.0.1', '--port', '8765', '--reload'], root)
run('web', process.execPath, [vite, '--host', '127.0.0.1', '--port', '3000'], frontend)
