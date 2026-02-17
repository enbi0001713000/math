require 'yaml'

doc = YAML.load_file('openapi.yaml')
paths = doc.fetch('paths')
schemas = doc.fetch('components').fetch('schemas')

refs = File.read('openapi.yaml').scan(%r{#/components/schemas/([A-Za-z0-9_]+)}).flatten.uniq
missing = refs.reject { |name| schemas.key?(name) }

if missing.any?
  warn "Missing schemas: #{missing.join(', ')}"
  exit 1
end

puts "OK: paths=#{paths.size} schemas=#{schemas.size} refs=#{refs.size}"
