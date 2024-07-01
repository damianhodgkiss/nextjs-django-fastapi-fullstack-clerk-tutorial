import { clerkMiddleware, createRouteMatcher} from '@clerk/nextjs/server';

const isPublicRoute = createRouteMatcher(['/', '/sign-in', '/sign-up']);

export default clerkMiddleware((auth, request) => {
  const opts = {};

  if (!isPublicRoute(request)) {
    auth().protect(opts);
  }
});

export const config = {
  matcher: ["/((?!.*\\..*|_next).*)", "/", "/(api|trpc)(.*)"],
}