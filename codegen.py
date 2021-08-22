from grpc_tools import protoc


protoc.main(
    (
        '',
        '-I.',
        '-I./venv/Lib/site-packages/grpc_tools/_proto',
        '--python_out=.',
        '--grpc_python_out=.',
        './chat.proto',
    )
)
