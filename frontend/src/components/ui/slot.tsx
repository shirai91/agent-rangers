import * as React from "react"

interface SlotProps extends React.HTMLAttributes<HTMLElement> {
  children?: React.ReactNode
}

interface SlotCloneProps {
  children: React.ReactElement
}

function mergeProps(slotProps: Record<string, unknown>, childProps: Record<string, unknown>) {
  const overrideProps: Record<string, unknown> = { ...childProps }

  for (const propName in childProps) {
    const slotPropValue = slotProps[propName]
    const childPropValue = childProps[propName]

    const isHandler = /^on[A-Z]/.test(propName)
    if (isHandler) {
      if (slotPropValue && childPropValue) {
        overrideProps[propName] = (...args: unknown[]) => {
          (childPropValue as (...args: unknown[]) => void)(...args);
          (slotPropValue as (...args: unknown[]) => void)(...args)
        }
      } else if (slotPropValue) {
        overrideProps[propName] = slotPropValue
      }
    } else if (propName === 'style') {
      overrideProps[propName] = { ...(slotPropValue as object), ...(childPropValue as object) }
    } else if (propName === 'className') {
      overrideProps[propName] = [slotPropValue, childPropValue].filter(Boolean).join(' ')
    }
  }

  return { ...slotProps, ...overrideProps }
}

const SlotClone = React.forwardRef<HTMLElement, SlotCloneProps>(
  (props, forwardedRef) => {
    const { children, ...slotProps } = props

    if (React.isValidElement(children)) {
      return React.cloneElement(children, {
        ...mergeProps(slotProps, children.props as Record<string, unknown>),
        ref: forwardedRef
          ? composeRefs(forwardedRef, (children as React.ReactElement & { ref?: React.Ref<unknown> }).ref)
          : (children as React.ReactElement & { ref?: React.Ref<unknown> }).ref,
      } as React.Attributes)
    }

    return null
  }
)
SlotClone.displayName = "SlotClone"

const Slot = React.forwardRef<HTMLElement, SlotProps>((props, forwardedRef) => {
  const { children, ...slotProps } = props

  const childrenArray = React.Children.toArray(children)
  const slottable = childrenArray.find(isSlottable)

  if (slottable) {
    const newElement = slottable.props.children as React.ReactNode

    const newChildren = childrenArray.map((child) => {
      if (child === slottable) {
        if (React.Children.count(newElement) > 1) {
          return React.Children.only(null)
        }
        return React.isValidElement(newElement)
          ? (newElement.props as { children?: React.ReactNode }).children
          : null
      } else {
        return child
      }
    })

    return (
      <SlotClone {...slotProps} ref={forwardedRef}>
        {React.isValidElement(newElement)
          ? React.cloneElement(newElement, undefined, newChildren)
          : null}
      </SlotClone>
    )
  }

  const child = React.Children.only(children)
  if (React.isValidElement(child)) {
    return (
      <SlotClone {...slotProps} ref={forwardedRef}>
        {child}
      </SlotClone>
    )
  }

  return null
})
Slot.displayName = "Slot"

const Slottable = ({ children }: { children: React.ReactNode }) => {
  return <>{children}</>
}

function isSlottable(child: React.ReactNode): child is React.ReactElement<{ children: React.ReactNode }> {
  return React.isValidElement(child) && child.type === Slottable
}

function composeRefs<T>(...refs: (React.Ref<T> | undefined)[]): React.RefCallback<T> {
  return (node) => {
    refs.forEach((ref) => {
      if (typeof ref === 'function') {
        ref(node)
      } else if (ref != null) {
        (ref as React.MutableRefObject<T | null>).current = node
      }
    })
  }
}

export { Slot, Slottable }
