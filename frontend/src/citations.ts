import type { Message } from './types'

export function citationTarget(message: Message, number: number) {
  const source = message.details.sources.find(source => source.numbers.includes(number))
  if (source) return source.url
  if (message.details.policies.some(policy => policy.number === number)) return `#source-${message.id}-${number}`
  return undefined
}

type Node = { type: string; value?: string; url?: string; children?: Node[] }

// Transform only plain-text citation markers, preserving existing links/code.
// Targets come from the server's validated source projection, never model URLs.
export function citationPlugin(message?: Message) {
  return () => (tree: Node) => {
    if (!message) return
    const visit = (parent: Node) => {
      if (['link', 'linkReference', 'code', 'inlineCode'].includes(parent.type) || !parent.children) return
      parent.children = parent.children.flatMap(node => {
        if (node.type !== 'text' || !node.value) { visit(node); return [node] }
        const result: Node[] = []
        let start = 0
        for (const match of node.value.matchAll(/\[(\d+)\]/g)) {
          const url = citationTarget(message, Number(match[1]))
          if (!url) continue
          if (match.index > start) result.push({ type: 'text', value: node.value.slice(start, match.index) })
          result.push({ type: 'link', url, children: [{ type: 'text', value: match[0] }] })
          start = match.index + match[0].length
        }
        if (!start) return [node]
        if (start < node.value.length) result.push({ type: 'text', value: node.value.slice(start) })
        return result
      })
    }
    visit(tree)
  }
}
