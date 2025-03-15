import { NextRequest, NextResponse } from 'next/server';

// This proxies API requests to your Flask backend
export async function GET(
  request: NextRequest,
  { params }: { params: { route: string[] } }
) {
  const route = params.route.join('/');
  const url = `http://localhost:5000/api/${route}${request.nextUrl.search}`;
  
  try {
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error(`Error proxying to ${url}:`, error);
    return NextResponse.json({ error: 'Failed to fetch data from API' }, { status: 500 });
  }
}

export async function POST(
  request: NextRequest,
  { params }: { params: { route: string[] } }
) {
  const route = params.route.join('/');
  const url = `http://localhost:5000/api/${route}`;
  
  try {
    const contentType = request.headers.get('content-type') || 'application/json';
    
    let body;
    if (contentType.includes('multipart/form-data')) {
      body = await request.formData();
    } else {
      body = await request.json();
    }
    
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': contentType,
      },
      body: contentType.includes('multipart/form-data') 
        ? body as FormData 
        : JSON.stringify(body),
    });
    
    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error(`Error proxying to ${url}:`, error);
    return NextResponse.json({ error: 'Failed to send data to API' }, { status: 500 });
  }
}