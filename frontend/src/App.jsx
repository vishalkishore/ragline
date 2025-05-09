import { useState, useEffect } from 'react'

function App() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [documents, setDocuments] = useState([])
  const [selectedDocuments, setSelectedDocuments] = useState([])
  const [uploadProgress, setUploadProgress] = useState({})
  const [isUploading, setIsUploading] = useState(false)

  // Fetch all documents on component mount
  useEffect(() => {
    fetchDocuments()
  }, [])

  const fetchDocuments = async () => {
    try {
      const response = await fetch('http://127.0.0.1:8000/documents/')
      const data = await response.json()
      setDocuments(data)
    } catch (error) {
      console.error('Error fetching documents:', error)
    }
  }

  const handleFileUpload = async (e) => {
    const files = e.target.files
    if (!files.length) return

    setIsUploading(true)

    for (let i = 0; i < files.length; i++) {
      const file = files[i]
      const formData = new FormData()
      formData.append('file', file)

      // Create unique ID for tracking this file's progress
      const uploadId = `upload-${Date.now()}-${i}`

      // Initialize progress tracking
      setUploadProgress((prev) => ({
        ...prev,
        [uploadId]: {
          filename: file.name,
          progress: 0,
          completed: false,
        },
      }))

      try {
        // Use XMLHttpRequest for upload progress tracking
        const xhr = new XMLHttpRequest()

        xhr.upload.onprogress = (event) => {
          if (event.lengthComputable) {
            const percentComplete = Math.round(
              (event.loaded / event.total) * 100
            )
            setUploadProgress((prev) => ({
              ...prev,
              [uploadId]: {
                ...prev[uploadId],
                progress: percentComplete,
              },
            }))
          }
        }

        xhr.onload = async () => {
          if (xhr.status === 200 || xhr.status === 201) {
            const response = JSON.parse(xhr.responseText)
            setUploadProgress((prev) => ({
              ...prev,
              [uploadId]: {
                ...prev[uploadId],
                completed: true,
              },
            }))

            // Add the uploaded document to our documents list
            setDocuments((prevDocs) => [...prevDocs, response])

            // Also select this document by default
            setSelectedDocuments((prev) => [...prev, response.id])

            // Clean up progress tracking after a delay
            setTimeout(() => {
              setUploadProgress((prev) => {
                const newProgress = { ...prev }
                delete newProgress[uploadId]
                return newProgress
              })
            }, 3000)
          }
        }

        xhr.onerror = () => {
          console.error('Upload failed')
          setUploadProgress((prev) => ({
            ...prev,
            [uploadId]: {
              ...prev[uploadId],
              error: true,
            },
          }))
        }

        xhr.open('POST', 'http://127.0.0.1:8000/documents/', true)
        xhr.send(formData)
      } catch (error) {
        console.error('Error uploading file:', error)
        setUploadProgress((prev) => ({
          ...prev,
          [uploadId]: {
            ...prev[uploadId],
            error: true,
          },
        }))
      }
    }

    // Reset file input
    e.target.value = ''
    setIsUploading(false)
  }

  const handleDocumentSelection = (docId) => {
    setSelectedDocuments((prev) => {
      if (prev.includes(docId)) {
        return prev.filter((id) => id !== docId)
      } else {
        return [...prev, docId]
      }
    })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()

    if (!input.trim() || selectedDocuments.length === 0) return

    // Add user message to chat
    const userMessage = {
      type: 'user',
      content: input,
      timestamp: new Date().toISOString(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      const response = await fetch('http://127.0.0.1:8000/query/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: input,
          document_ids: selectedDocuments,
          top_k: 3,
        }),
      })

      const data = await response.json()

      const aiMessage = {
        type: 'ai',
        content: data.answer,
        documents: data.documents,
        timestamp: new Date().toISOString(),
      }

      setMessages((prev) => [...prev, aiMessage])
    } catch (error) {
      console.error('Error querying documents:', error)

      const errorMessage = {
        type: 'error',
        content:
          'An error occurred while processing your query. Please try again.',
        timestamp: new Date().toISOString(),
      }

      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  // Calculate if we should disable the input
  const isInputDisabled =
    isUploading ||
    Object.values(uploadProgress).some((p) => !p.completed && !p.error)

  return (
    <div className="flex h-screen bg-white dark:bg-gray-800">
      {/* Sidebar */}
      <div className="w-80 bg-gray-50 dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700 flex flex-col">
        {/* Sidebar Header */}
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-medium text-gray-800 dark:text-gray-200">
            Documents
          </h2>
        </div>

        {/* Upload Button */}
        <div className="p-4">
          <label className="flex items-center justify-center w-full px-4 py-2.5 bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-800 dark:text-gray-200 rounded-md cursor-pointer transition-colors duration-200">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-5 w-5 mr-2"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fillRule="evenodd"
                d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM6.293 6.707a1 1 0 010-1.414l3-3a1 1 0 011.414 0l3 3a1 1 0 01-1.414 1.414L11 5.414V13a1 1 0 11-2 0V5.414L7.707 6.707a1 1 0 01-1.414 0z"
                clipRule="evenodd"
              />
            </svg>
            Upload PDF
            <input
              type="file"
              className="hidden"
              accept=".pdf"
              multiple
              onChange={handleFileUpload}
            />
          </label>
        </div>

        {/* Upload Progress */}
        {Object.entries(uploadProgress).length > 0 && (
          <div className="px-4 pb-4">
            <h3 className="text-xs font-medium text-gray-600 dark:text-gray-400 mb-2">
              Uploading
            </h3>
            <div className="space-y-2">
              {Object.entries(uploadProgress).map(
                ([id, { filename, progress, completed, error }]) => (
                  <div key={id} className="text-xs">
                    <div className="flex justify-between mb-1">
                      <span className="truncate text-gray-800 dark:text-gray-300">
                        {filename}
                      </span>
                      <span
                        className={
                          error
                            ? 'text-red-500'
                            : completed
                              ? 'text-green-500'
                              : 'text-gray-600 dark:text-gray-400'
                        }
                      >
                        {completed ? 'Done' : error ? 'Error' : `${progress}%`}
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1">
                      <div
                        className={`h-1 rounded-full ${error ? 'bg-red-500' : completed ? 'bg-green-500' : 'bg-blue-500'}`}
                        style={{ width: `${progress}%` }}
                      ></div>
                    </div>
                  </div>
                )
              )}
            </div>
          </div>
        )}

        {/* Document List */}
        <div className="flex-grow overflow-y-auto border-t border-gray-200 dark:border-gray-700">
          {documents.length === 0 ? (
            <div className="p-6 text-center text-gray-500 dark:text-gray-400">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-12 w-12 mx-auto mb-3 text-gray-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
              <p>No documents uploaded yet</p>
            </div>
          ) : (
            <div className="py-2">
              {documents.map((doc) => (
                <div
                  key={doc.id}
                  className={`flex items-center px-4 py-3 cursor-pointer transition-colors duration-200 ${
                    selectedDocuments.includes(doc.id)
                      ? 'bg-gray-100 dark:bg-gray-800 border-l-4 border-blue-500'
                      : 'hover:bg-gray-100 dark:hover:bg-gray-800 border-l-4 border-transparent'
                  }`}
                  onClick={() => handleDocumentSelection(doc.id)}
                >
                  <input
                    type="checkbox"
                    className="mr-3 h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    checked={selectedDocuments.includes(doc.id)}
                    onChange={() => {}} // Handled by the parent div's onClick
                  />
                  <div className="truncate">
                    <div className="text-sm font-medium text-gray-800 dark:text-gray-200 truncate">
                      {doc.filename}
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400">
                      {doc.page_count || '?'} pages
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Chat Messages */}
        <div className="flex-1 overflow-y-auto p-4 bg-white dark:bg-gray-800">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center">
              <div className="text-5xl mb-6">💬</div>
              <h1 className="text-2xl font-bold mb-2 text-gray-800 dark:text-gray-200">
                Document Chat
              </h1>
              <p className="text-gray-500 dark:text-gray-400 max-w-md">
                Upload PDF documents from the sidebar and ask questions about
                their content
              </p>
            </div>
          ) : (
            <div className="max-w-3xl mx-auto space-y-6">
              {messages.map((msg, idx) => (
                <div
                  key={idx}
                  className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`rounded-lg p-4 max-w-[85%] ${
                      msg.type === 'user'
                        ? 'bg-blue-500 text-white'
                        : msg.type === 'error'
                          ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                          : 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200'
                    }`}
                  >
                    <div className="text-sm whitespace-pre-wrap">
                      {msg.content}
                    </div>

                    {/* Document references */}
                    {msg.documents && msg.documents.length > 0 && (
                      <div className="mt-4 pt-3 border-t border-gray-200 dark:border-gray-600">
                        <h4 className="text-xs font-semibold text-gray-500 dark:text-gray-400 mb-2">
                          SOURCES
                        </h4>
                        <div className="space-y-2">
                          {msg.documents.map((doc, docIdx) => (
                            <div
                              key={docIdx}
                              className="text-xs bg-white dark:bg-gray-800 p-2 rounded border border-gray-200 dark:border-gray-600"
                            >
                              <div className="flex justify-between mb-1">
                                <span className="font-medium text-gray-800 dark:text-gray-200">
                                  {doc.filename}
                                </span>
                                <span className="text-gray-500 dark:text-gray-400">
                                  Page {doc.page_num}
                                </span>
                              </div>
                              <p className="text-gray-600 dark:text-gray-300">
                                {doc.content}
                              </p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {isLoading && (
                <div className="flex justify-start">
                  <div className="bg-gray-100 dark:bg-gray-700 rounded-lg p-4">
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                      <div
                        className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                        style={{ animationDelay: '0.2s' }}
                      ></div>
                      <div
                        className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                        style={{ animationDelay: '0.4s' }}
                      ></div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Input Box */}
        <div className="p-4 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
          <div className="max-w-3xl mx-auto">
            <form onSubmit={handleSubmit} className="flex items-center">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                disabled={isInputDisabled || isLoading}
                placeholder={
                  isInputDisabled
                    ? 'Uploading documents...'
                    : 'Ask a question about your documents'
                }
                className="flex-1 bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200 border border-gray-200 dark:border-gray-600 rounded-lg py-3 px-4 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <button
                type="submit"
                disabled={
                  isInputDisabled ||
                  isLoading ||
                  !input.trim() ||
                  selectedDocuments.length === 0
                }
                className="ml-2 p-3 rounded-lg bg-blue-500 hover:bg-blue-600 text-white disabled:bg-blue-400 disabled:opacity-50 transition-colors duration-200"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-5 w-5"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    fillRule="evenodd"
                    d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z"
                    clipRule="evenodd"
                  />
                </svg>
              </button>
            </form>

            <div className="flex justify-between mt-2 text-xs text-gray-500 dark:text-gray-400">
              <div>
                {selectedDocuments.length === 0 ? (
                  <span>No documents selected</span>
                ) : (
                  <span>
                    {selectedDocuments.length} document
                    {selectedDocuments.length !== 1 ? 's' : ''} selected
                  </span>
                )}
              </div>
              {selectedDocuments.length === 0 && documents.length > 0 && (
                <div className="text-blue-500 dark:text-blue-400">
                  Select documents from the sidebar to start chatting
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
