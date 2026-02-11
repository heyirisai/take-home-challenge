import Link from "next/link";

interface CardProps {
  title: string;
  description: string;
  href?: string;
  linkText?: string;
  children?: React.ReactNode;
}

export function Card({ title, description, href, linkText, children }: CardProps) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm transition-shadow hover:shadow-md">
      <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
      <p className="mt-2 text-sm text-gray-600">{description}</p>
      {children}
      {href && linkText && (
        <div className="mt-4">
          <Link
            href={href}
            className="text-sm font-medium text-indigo-600 hover:text-indigo-500"
          >
            {linkText} &rarr;
          </Link>
        </div>
      )}
    </div>
  );
}
